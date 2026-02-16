import abc
import logging
import typing
from typing import Any, Dict, Generic, TypeVar
from pathlib import Path
from pydantic import ConfigDict, BaseModel, Field

if typing.TYPE_CHECKING:
    # Cyclic import
    from super.core.environment.simple import EnvSettings


def UserConfigurable(*args, **kwargs):
    return Field(*args, **kwargs, user_configurable=True)


class SystemConfiguration(BaseModel):
    def get_user_config(self) -> Dict[str, Any]:
        return _get_user_config_fields(self)

    model_config = ConfigDict(
        extra="forbid", use_enum_values=True, arbitrary_types_allowed=True
    )


class SystemSettings(BaseModel):
    """A base class for all system settings."""

    name: str
    description: str
    model_config = ConfigDict(extra="forbid", use_enum_values=True)


S = TypeVar("S", bound=SystemSettings)


class Configurable(abc.ABC, Generic[S]):
    """A base class for all configurable objects."""

    prefix: str = ""
    default_settings: typing.ClassVar[S]

    @classmethod
    def get_user_config(cls) -> Dict[str, Any]:
        return _get_user_config_fields(cls.default_settings)

    @classmethod
    def build_configuration(cls, configuration: dict) -> S:
        """Process the configuration for this object."""

        defaults = cls.default_settings.dict()
        final_configuration = deep_update(defaults, configuration)

        return cls.default_settings.__class__.model_validate(final_configuration)


def _get_user_config_fields(instance: BaseModel) -> Dict[str, Any]:
    """
    Get the user config fields of a Pydantic model instance.

    Args:
        instance: The Pydantic model instance.

    Returns:
        The user config fields of the instance.
    """
    user_config_fields = {}

    for name, value in instance.__dict__.items():
        field_info = instance.__fields__[name]
        if "user_configurable" in field_info.field_info.extra:
            user_config_fields[name] = value
        elif isinstance(value, SystemConfiguration):
            user_config_fields[name] = value.get_user_config()
        elif isinstance(value, list) and all(
            isinstance(i, SystemConfiguration) for i in value
        ):
            user_config_fields[name] = [i.get_user_config() for i in value]
        elif isinstance(value, dict) and all(
            isinstance(i, SystemConfiguration) for i in value.values()
        ):
            user_config_fields[name] = {
                k: v.get_user_config() for k, v in value.items()
            }

    return user_config_fields


def deep_update(original_dict: dict, update_dict: dict) -> dict:
    """
    Recursively update a dictionary.

    Args:
        original_dict (dict): The dictionary to be updated.
        update_dict (dict): The dictionary to update with.

    Returns:
        dict: The updated dictionary.
    """
    for key, value in update_dict.items():
        if (
            key in original_dict
            and isinstance(original_dict[key], dict)
            and isinstance(value, dict)
        ):
            original_dict[key] = deep_update(original_dict[key], value)
        else:
            original_dict[key] = value
    return original_dict


class WorkspaceConfiguration(SystemConfiguration):
    root: str
    parent: str = UserConfigurable()
    restrict_to_workspace: bool = UserConfigurable()


class WorkspaceSettings(SystemSettings):
    configuration: WorkspaceConfiguration


class WorkspaceSetup(abc.ABC):
    @staticmethod
    def setup_workspace(
        settings: "EnvSettings",
        logger: logging.Logger,
        config_name: str,
        save_file=True,
    ) -> Path:
        workspace_parent = settings.workspace.configuration.parent
        workspace_parent = Path(workspace_parent).expanduser().resolve()
        workspace_parent.mkdir(parents=True, exist_ok=True)

        environment_name = settings.environment.name

        workspace_root = workspace_parent / environment_name
        workspace_root.mkdir(parents=True, exist_ok=True)

        settings.workspace.configuration.root = str(workspace_root)

        settings_json = settings.model_dump_json()
        if save_file:
            with (workspace_root / f"{config_name}_settings.json").open("w") as f:
                f.write(settings_json)

        # TODO: What are all the kinds of logs we want here?
        log_path = workspace_root / "logs"
        log_path.mkdir(parents=True, exist_ok=True)
        (log_path / "debug.log").touch()
        (log_path / "cycle.log").touch()

        return workspace_root if save_file else settings_json

    @staticmethod
    def load_environment_settings(
        workspace_root: Path, config_name: str
    ) -> "EnvSettings":
        # Cyclic import
        from super.core.environment.simple import EnvSettings
        import json

        with (workspace_root / f"{config_name}_settings.json").open("r") as f:
            environment_settings = json.load(f)

        return EnvSettings.model_validate(environment_settings)

    @staticmethod
    def load_environment_settings_goal(
        goal: str, request_id: str, config_name: str
    ) -> "EnvSettings":
        # Cyclic import
        from super.core.environment.simple import EnvSettings

        # from super.core.configuration.goal import fetch_goal

        # goal = fetch_goal(goal, request_id, config_name)
        environment_settings = goal.get("settings_json", {})
        return EnvSettings.model_validate(environment_settings)

    @staticmethod
    def save_environment_settings_goal(goal: str, request_id: str, settings_json: Dict):
        # Cyclic import
        from super.core.configuration.goal import save_goal, config_to_goal

        goal = config_to_goal(goal, request_id, settings_json)
        goal = save_goal(goal)
        return goal
