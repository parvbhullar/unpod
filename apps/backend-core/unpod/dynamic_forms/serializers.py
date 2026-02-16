from rest_framework import serializers

from .models import (
    DynamicForm,
    FormFields,
    FormFieldDependency,
    FormFieldOptionsApi,
    DynamicFormValues,
)


class DynamicFormSerializer(serializers.ModelSerializer):
    form_fields = serializers.SerializerMethodField()
    form_values = serializers.SerializerMethodField()
    # author = serializers.CharField(source="created_by.username", read_only=True)

    class Meta:
        model = DynamicForm
        fields = [
            "id",
            "name",
            "slug",
            "description",
            # "status",
            # "author",
            "form_fields",
            "form_values",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    @staticmethod
    def get_form_fields(obj):
        fields = FormFields.objects.filter(form=obj, status="active")
        serializer = DynamicFormFieldSerializer(fields, many=True)
        return serializer.data

    @staticmethod
    def get_form_values(obj):
        form_values = DynamicFormValues.objects.filter(form=obj).first()
        serializer = DynamicFormValuesSerializer(form_values, many=False)

        if serializer.instance is None:
            return None

        return serializer.data


class DynamicFormValuesSerializer(serializers.ModelSerializer):
    class Meta:
        model = DynamicFormValues
        fields = [
            "id",
            "name",
            "parent_type",
            "parent_id",
            "form",
            "values",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class FormFieldOptionsApiSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormFieldOptionsApi
        fields = [
            "id",
            "title",
            "endpoint",
            "method",
            "headers",
            "params",
            "value_key",
            "label_key",
        ]
        read_only_fields = [
            "id",
        ]


class DynamicFormFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormFields
        fields = [
            "id",
            "title",
            "placeholder",
            "type",
            "name",
            "description",
            "default",
            "required",
            "regex",
            "config",
            "options_type",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        if instance.options_type == "static":
            representation["options"] = instance.options
        elif instance.options_type == "api":
            # Serialize options_api using FormFieldOptionsApiSerializer
            if instance.options_api:
                representation["options_api"] = FormFieldOptionsApiSerializer(
                    instance.options_api
                ).data
            else:
                representation["options_api"] = None

        # Serialize dependencies using FormFieldDependencySerializer
        dependencies = FormFieldDependency.objects.filter(
            field=instance, status="active"
        )
        representation["dependencies"] = FormFieldDependencySerializer(
            dependencies, many=True
        ).data
        return representation


class FormFieldDependencySerializer(serializers.ModelSerializer):
    depends_on = serializers.CharField(source="depends_on_field.name", read_only=True)

    class Meta:
        model = FormFieldDependency
        fields = [
            "depends_on",
            "condition",
            "value",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
