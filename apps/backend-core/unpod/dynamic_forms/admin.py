from django.conf import settings
from django.contrib import admin
from django.utils.html import format_html
from import_export.admin import ImportExportActionModelAdmin


from .models import (
    DynamicForm,
    FormFields,
    FormFieldDependency,
    FormFieldOptionsApi,
    DynamicFormValues,
)
from ..common.mixin import UnpodCustomModelAdmin


class FormFieldsInline(admin.TabularInline):
    model = FormFields
    extra = 0
    fields = (
        "id",
        "title",
        "type",
        "name",
        "required",
        "sort_order",
        "status",
    )
    readonly_fields = [
        "id",
        "title",
        "type",
        "name",
        "status",
    ]
    # fields = ["title", "name"]
    show_change_link = True  # adds link to full book edit page
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False  # ❌ disables the "Add another book" button


@admin.register(DynamicForm)
class DynamicFormAdmin(UnpodCustomModelAdmin):
    list_display = (
        "id",
        "name",
        "parent_type",
        "slug",
        "status",
        "sort_order",
        "username",
        "created_at",
    )
    list_editable = ["status", "sort_order"]  # editable directly in list
    search_fields = ("name", "description")
    list_filter = ("status", "group_key", "created_by")
    inlines = [FormFieldsInline]

    def username(self, obj):
        if obj.created_by:
            name = obj.created_by.username

            if obj.created_by.first_name or obj.created_by.last_name:
                name = f"{obj.created_by.first_name} {obj.created_by.last_name}"

            return format_html(
                '<a href="/{}users/user/{}/change/"  target="_blank">{}</a>',
                settings.ADMIN_URL,
                obj.created_by.id,
                name,
            )

        return obj.created_by

    username.short_description = "Created by"


@admin.register(DynamicFormValues)
class DynamicFormValuesAdmin(UnpodCustomModelAdmin):
    list_display = (
        "id",
        "name",
        "parent_type",
        "parent_id",
        "form",
        "username",
        "created_at",
    )
    search_fields = ("name", "parent_type")
    list_filter = ("parent_type", "form", "created_by")

    def username(self, obj):
        if obj.created_by:
            name = obj.created_by.username

            if obj.created_by.first_name or obj.created_by.last_name:
                name = f"{obj.created_by.first_name} {obj.created_by.last_name}"

            return format_html(
                '<a href="/{}users/user/{}/change/"  target="_blank">{}</a>',
                settings.ADMIN_URL,
                obj.created_by.id,
                name,
            )

        return obj.created_by

    username.short_description = "Created by"


@admin.register(FormFieldOptionsApi)
class FormFieldOptionsApiAdmin(UnpodCustomModelAdmin):
    list_display = ("id", "title", "endpoint", "value_key", "label_key")
    search_fields = ("title", "endpoint")
    list_filter = ("method",)


class DependencyInline(admin.TabularInline):
    model = FormFieldDependency
    fk_name = "field"
    extra = 0


@admin.register(FormFields)
class FormFieldsAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):
    list_display = (
        "id",
        "title",
        "type",
        "name",
        "form_name",
        "required",
        "sort_order",
        "status",
        "username",
        "created_at",
    )
    list_editable = ["required", "status", "sort_order"]  # editable directly in list
    search_fields = ("name", "description")
    list_filter = ("form", "status")
    inlines = [DependencyInline]

    class Media:
        js = ("js/show_hide_fields.js",)  # load custom JS

    def username(self, obj):
        if obj.created_by:
            name = obj.created_by.username

            if obj.created_by.first_name or obj.created_by.last_name:
                name = f"{obj.created_by.first_name} {obj.created_by.last_name}"

            return format_html(
                '<a href="/{}users/user/{}/change/"  target="_blank">{}</a>',
                settings.ADMIN_URL,
                obj.created_by.id,
                name,
            )

        return obj.created_by

    username.short_description = "Created by"

    def form_name(self, obj):
        if obj.form:
            name = obj.form.name

            return format_html(
                '<a href="/{}dynamic_forms/dynamicform/{}/change/"  target="_blank">{}</a>',
                settings.ADMIN_URL,
                obj.form.id,
                name,
            )

        return obj.form

    form_name.short_description = "Form"


@admin.register(FormFieldDependency)
class FormFieldDependencyAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):
    list_display = (
        "id",
        "field",
        "dependency_field",
        "depends_on_field",
        "condition",
        "value",
        "status",
        "username",
        "created_at",
    )
    search_fields = ("field__name", "value")
    list_filter = ("field", "field__form", "status")

    def username(self, obj):
        if obj.created_by:
            name = obj.created_by.username

            if obj.created_by.first_name or obj.created_by.last_name:
                name = f"{obj.created_by.first_name} {obj.created_by.last_name}"

            return format_html(
                '<a href="/{}users/user/{}/change/"  target="_blank">{}</a>',
                settings.ADMIN_URL,
                obj.created_by.id,
                name,
            )

        return obj.created_by

    username.short_description = "Created by"

    def dependency_field(self, obj):
        if obj.depends_on_field:
            name = obj.depends_on_field.title

            return format_html(
                '<a href="/{}dynamic_forms/formfields/{}/change/"  target="_blank">{}</a>',
                settings.ADMIN_URL,
                obj.depends_on_field.id,
                name,
            )

        return obj.depends_on_field

    dependency_field.short_description = "Depends On Field"
