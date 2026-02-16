import ast
import copy
import json
import logging
import os
import yaml
from hashlib import md5
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

T = TypeVar("T", bound="JsonSerializableRegistry")


class JsonSerializableRegistry:
    class_mapping = {}

    def to_json(
        self, include: list = None, suppress: list = None, file_path: str = None
    ) -> dict:
        serializable_attrs = set()
        suppress_attrs = set()
        for cls in self.__class__.__mro__:
            if hasattr(cls, "serializable_attributes") and isinstance(
                cls.serializable_attributes, list
            ):
                serializable_attrs.update(cls.serializable_attributes)
            if hasattr(cls, "suppress_attributes_from_serialization") and isinstance(
                cls.suppress_attributes_from_serialization, list
            ):
                suppress_attrs.update(cls.suppress_attributes_from_serialization)

        if include:
            serializable_attrs = set(include)
        if suppress:
            suppress_attrs.update(suppress)

        result = {"json_serializable_class_name": self.__class__.__name__}
        for attr in serializable_attrs if serializable_attrs else self.__dict__:
            if attr not in suppress_attrs:
                value = getattr(self, attr, None)
                if isinstance(value, JsonSerializableRegistry):
                    result[attr] = value.to_json()
                elif isinstance(value, list):
                    result[attr] = [
                        item.to_json()
                        if isinstance(item, JsonSerializableRegistry)
                        else copy.deepcopy(item)
                        for item in value
                    ]
                elif isinstance(value, dict):
                    result[attr] = {
                        k: v.to_json()
                        if isinstance(v, JsonSerializableRegistry)
                        else copy.deepcopy(v)
                        for k, v in value.items()
                    }
                else:
                    result[attr] = copy.deepcopy(value)

        if file_path:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w") as f:
                json.dump(result, f, indent=4)

        return result

    @classmethod
    def from_json(
        cls: Type[T],
        json_dict_or_path: Union[Dict[str, Any], str],
        suppress: list = None,
        post_init_params: dict = None,
    ) -> T:
        if isinstance(json_dict_or_path, str):
            with open(json_dict_or_path, "r") as f:
                json_dict = json.load(f)
        else:
            json_dict = json_dict_or_path

        subclass_name = json_dict.get("json_serializable_class_name")
        target_class = cls.class_mapping.get(subclass_name, cls)
        instance = target_class.__new__(target_class)

        serializable_attrs = set()
        custom_serialization_initializers = {}
        suppress_attrs = set(suppress) if suppress else set()
        for cls in target_class.__mro__:
            if hasattr(cls, "serializable_attributes") and isinstance(
                cls.serializable_attributes, list
            ):
                serializable_attrs.update(cls.serializable_attributes)
            if hasattr(cls, "custom_serialization_initializers") and isinstance(
                cls.custom_serialization_initializers, dict
            ):
                custom_serialization_initializers.update(
                    cls.custom_serialization_initializers
                )
            if hasattr(cls, "suppress_attributes_from_serialization") and isinstance(
                cls.suppress_attributes_from_serialization, list
            ):
                suppress_attrs.update(cls.suppress_attributes_from_serialization)

        for key in serializable_attrs if serializable_attrs else json_dict:
            if key in json_dict and key not in suppress_attrs:
                value = json_dict[key]
                if key in custom_serialization_initializers:
                    setattr(
                        instance, key, custom_serialization_initializers[key](value)
                    )
                elif (
                    isinstance(value, dict) and "json_serializable_class_name" in value
                ):
                    setattr(instance, key, JsonSerializableRegistry.from_json(value))
                elif isinstance(value, list):
                    deserialized_collection = []
                    for item in value:
                        if (
                            isinstance(item, dict)
                            and "json_serializable_class_name" in item
                        ):
                            deserialized_collection.append(
                                JsonSerializableRegistry.from_json(item)
                            )
                        else:
                            deserialized_collection.append(copy.deepcopy(item))
                    setattr(instance, key, deserialized_collection)
                else:
                    setattr(instance, key, copy.deepcopy(value))

        if hasattr(instance, "_post_deserialization_init") and callable(
            instance._post_deserialization_init
        ):
            post_init_params = post_init_params if post_init_params else {}
            instance._post_deserialization_init(**post_init_params)

        return instance

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        JsonSerializableRegistry.class_mapping[cls.__name__] = cls

        if hasattr(cls, "serializable_attributes") and isinstance(
            cls.serializable_attributes, list
        ):
            for base in cls.__bases__:
                if hasattr(base, "serializable_attributes") and isinstance(
                    base.serializable_attributes, list
                ):
                    cls.serializable_attributes = list(
                        set(base.serializable_attributes + cls.serializable_attributes)
                    )

        if hasattr(cls, "suppress_attributes_from_serialization") and isinstance(
            cls.suppress_attributes_from_serialization, list
        ):
            for base in cls.__bases__:
                if hasattr(
                    base, "suppress_attributes_from_serialization"
                ) and isinstance(base.suppress_attributes_from_serialization, list):
                    cls.suppress_attributes_from_serialization = list(
                        set(
                            base.suppress_attributes_from_serialization
                            + cls.suppress_attributes_from_serialization
                        )
                    )

        if hasattr(cls, "custom_serialization_initializers") and isinstance(
            cls.custom_serialization_initializers, dict
        ):
            for base in cls.__bases__:
                if hasattr(base, "custom_serialization_initializers") and isinstance(
                    base.custom_serialization_initializers, dict
                ):
                    base_initializers = base.custom_serialization_initializers.copy()
                    base_initializers.update(cls.custom_serialization_initializers)
                    cls.custom_serialization_initializers = base_initializers

    def _post_deserialization_init(self, **kwargs):
        if hasattr(self, "_post_init"):
            self._post_init(**kwargs)


def read_yaml(path: str) -> Dict[str, Any]:
    try:
        with open(path, "r") as file:
            return yaml.safe_load(file)
    except Exception as e:
        raise ValueError(f"Yaml loading failed due to: {e}")


def write_yaml(path: str, content: Dict[str, Any]):
    try:
        with open(path, "w") as file:
            yaml.safe_dump(content, file, sort_keys=False)
    except Exception as e:
        raise ValueError(f"Yaml writing failed due to: {e}")


def import_module(module_name: str):
    import importlib

    return importlib.import_module(module_name)


def json_loads(json_str: str):
    try:
        return json.loads(json_str)
    except json.decoder.JSONDecodeError as e:
        try:
            print(f"json decode error {e}. trying literal eval")
            return ast.literal_eval(json_str)
        except Exception as ex:
            try:
                json_str = json_str.replace("'s", "")
                return ast.literal_eval(json_str)
            except Exception as ex2:
                raise ex2
            raise ex


def generate_md5_hash(content: str) -> str:
    return md5(content.encode()).hexdigest()


def create_id(length: int = 4) -> str:
    import secrets
    from datetime import datetime

    date_str = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    ran_str = secrets.token_hex(length)
    return f"{date_str}-{ran_str}"
