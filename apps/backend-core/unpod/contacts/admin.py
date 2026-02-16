import csv

from django.contrib import admin
from django.http import HttpResponse

from .models import Contact
from ..common.mixin import UnpodCustomModelAdmin


@admin.action(description="Export selected contacts to CSV")
def export_contacts_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = "attachment; filename=users.csv"

    writer = csv.writer(response)
    writer.writerow(
        ["Username", "Email", "Business", "Phone", "Alternative Phone", "Products"]
    )

    for contact in queryset:
        writer.writerow(
            [
                contact.name,
                contact.email,
                contact.business,
                contact.phone,
                contact.alt_phone,
                contact.products,
            ]
        )

    return response


@admin.register(Contact)
class ContactAdmin(UnpodCustomModelAdmin):
    list_display = (
        "id",
        "name",
        "email",
        "user",
        "registered_as_user",
        "user_register_date",
        "business",
        "phone",
        "products",
        "status",
    )
    search_fields = ("name", "email", "business", "phone", "alt_phone")
    list_filter = ("products", "status", "registered_as_user", "user_register_date")
    readonly_fields = ("user_register_date",)
    actions = [export_contacts_csv]

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("name", "email", "business", "phone", "alt_phone")},
        ),
        (
            "Registration Info",
            {"fields": ("user", "registered_as_user", "user_register_date")},
        ),
        ("Other Information", {"fields": ("products", "status")}),
    )
