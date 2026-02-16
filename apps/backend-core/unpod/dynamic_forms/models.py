from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.utils.text import slugify

from unpod.common.enum import ModelBasicStatus, FormInputTypes, FormOptionsType
from unpod.common.query import unique_slugify
from .constants import TYPE_CHOICES, PARENT_TYPE_CHOICES


class DynamicForm(models.Model):
    name = models.CharField(max_length=100, help_text="Name of the form")
    slug = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        null=True,
    )
    description = models.TextField(blank=True, help_text="Description of the form")
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default="form",
    )
    parent_type = models.CharField(
        max_length=20,
        choices=PARENT_TYPE_CHOICES,
        default="individual",
    )
    group_key = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Group key to categorize forms",
    )
    status = models.CharField(
        max_length=20,
        choices=ModelBasicStatus.choices(),
        default=ModelBasicStatus.active.name,
        db_index=True,
    )
    sort_order = models.PositiveIntegerField(default=0, help_text="Order of the form")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "dynamic_forms"
        verbose_name = "Dynamic Form"
        verbose_name_plural = "Dynamic Forms"
        ordering = ["sort_order"]  # 👈 default order


class DynamicFormValues(models.Model):
    name = models.CharField(max_length=100, help_text="Name of the form")
    parent_type = models.CharField(
        max_length=20,
        choices=PARENT_TYPE_CHOICES,
        default="individual",
    )
    parent_id = models.CharField(
        max_length=100, blank=True, null=True, help_text="ID of the parent entity"
    )
    form = models.ForeignKey(
        DynamicForm, related_name="form_values", on_delete=models.SET_NULL, null=True
    )
    values = models.JSONField(
        help_text="Form field values in JSON format",
        blank=True,
        null=True,
        encoder=DjangoJSONEncoder,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "dynamic_form_values"
        verbose_name = "Dynamic Form Value"
        verbose_name_plural = "Dynamic Form Values"


class FormFieldOptionsApi(models.Model):
    title = models.CharField(max_length=255)
    endpoint = models.CharField(
        max_length=255, help_text="API endpoint to fetch options"
    )
    method = models.CharField(
        max_length=10,
        choices=[("GET", "GET"), ("POST", "POST")],
        default="GET",
        help_text="HTTP method to use",
    )
    headers = models.JSONField(
        blank=True,
        null=True,
        help_text="Headers to include in the API request in JSON format",
    )
    params = models.JSONField(
        blank=True,
        null=True,
        help_text="Query parameters to include in the API request in JSON format",
    )
    value_key = models.CharField(
        max_length=100,
        help_text="Key in the API response to use as the option value",
        default="id",
    )
    label_key = models.CharField(
        max_length=100,
        help_text="Key in the API response to use as the option label",
        default="title",
    )

    def __str__(self):
        return self.title

    class Meta:
        db_table = "dynamic_form_field_options_api"
        verbose_name = "Field Options API"
        verbose_name_plural = "Field Options APIs"


class FormFields(models.Model):
    form = models.ForeignKey(
        DynamicForm, related_name="fields", on_delete=models.CASCADE
    )
    title = models.CharField(max_length=255)
    placeholder = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True)
    type = models.CharField(
        max_length=20,
        choices=FormInputTypes.choices(),
        default=FormInputTypes.text.name,
        db_index=True,
    )
    name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Unique field name for the form",
    )
    default = models.CharField(max_length=255, blank=True, null=True)
    required = models.BooleanField(default=False)
    regex = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Regular expression for validation",
    )
    options_type = models.CharField(
        max_length=20,
        choices=FormOptionsType.choices(),
        blank=True,
        null=True,
    )
    options_api = models.ForeignKey(
        FormFieldOptionsApi,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text="API details to fetch options dynamically",
    )
    options = models.JSONField(
        blank=True,
        null=True,
        help_text="Options for select, radio, checkbox fields in JSON " "format",
    )
    config = models.JSONField(
        blank=True,
        null=True,
        encoder=DjangoJSONEncoder,
        help_text="Additional configuration for the field in JSON format",
    )
    sort_order = models.PositiveIntegerField(
        default=0, help_text="Order of the field in the form"
    )
    status = models.CharField(
        max_length=20,
        choices=ModelBasicStatus.choices(),
        default=ModelBasicStatus.active.name,
        db_index=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = slugify(self.title).replace("-", "_")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        db_table = "dynamic_form_fields"
        verbose_name = "Dynamic Form Field"
        verbose_name_plural = "Dynamic Form Fields"
        ordering = ["sort_order"]  # 👈 default order


class FormFieldDependency(models.Model):
    condition_choices = [
        ("equals", "Equals"),
        ("not_equals", "Not Equals"),
        ("starts_with", "Starts With"),
        ("ends_with", "Ends With"),
        ("is_empty", "Is Empty"),
        ("is_not_empty", "Is Not Empty"),
        ("contains", "Contains"),
        ("not_contains", "Not Contains"),
        # ("greater_than", "Greater Than"),
        # ("less_than", "Less Than"),
        # ("greater_than_equals", "Greater Than Equals"),
        # ("less_than_equals", "Less Than Equals"),
        # ("in", "In"),
        # ("not_in", "Not In"),
    ]

    field = models.ForeignKey(
        FormFields, related_name="dependents", on_delete=models.CASCADE
    )
    depends_on_field = models.ForeignKey(
        FormFields,
        related_name="dependency_fields",
        on_delete=models.SET_NULL,
        help_text="Field that this field depends on",
        null=True,
        default=None,
    )
    condition = models.CharField(
        max_length=20,
        choices=condition_choices,
        default="equals",
        help_text="Condition to evaluate",
    )
    value = models.CharField(
        max_length=255,
        help_text="The value of the depends_on field that triggers this field",
    )
    status = models.CharField(
        max_length=20,
        choices=ModelBasicStatus.choices(),
        default=ModelBasicStatus.active.name,
        db_index=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.field.name} depends on {self.depends_on_field.name} {self.condition} {self.value}"

    class Meta:
        db_table = "dynamic_form_field_dependencies"
        verbose_name = "Field Dependency"
        verbose_name_plural = "Field Dependencies"
