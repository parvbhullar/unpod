import os

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from import_export.admin import ImportExportActionModelAdmin

from .models import (
    ProviderCredential,
    VoiceBridge,
    VoiceBridgeNumber,
    BridgeProviderConfig,
)
from ..common.enum import DocumentStatus
from ..common.mixin import UnpodCustomModelAdmin
from ..documents.models import Document
from django.conf import settings

@admin.register(ProviderCredential)
class ProviderCredentialAdmin(UnpodCustomModelAdmin):
    list_display = ("id", "name", "provider", "organization_id", "organization", "active")
    search_fields = ("name", "provider__name", "organization__name")
    list_filter = ("active",)


@admin.register(VoiceBridge)
class VoiceBridgeAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):
    list_display = ("id", "name", "status", "documents_status", "product_id", "organization")
    search_fields = ("name",)
    list_filter = ("status", "documents_status")
    readonly_fields = ("related_documents",)

    fieldsets = [
        (
            None,
            {
                "fields": (
                    "name",
                    "description",
                    "status",
                    "slug",
                    "token",
                    "documents_status",
                    "region",
                    "product_id",
                    "organization",
                )
            },
        ),
        (
            "Documents",
            {
                "fields": ("related_documents",),
                # 'classes': ('collapse',)
            },
        ),
    ]

    def related_documents(self, bridge):
        documents = Document.objects.filter(
            module_type="bridge", module_object_id=bridge.slug
        )
        print("Related Documents:", documents, bridge)
        if not documents.exists():
            return format_html(f"""<p>No documents.</p>""")

        def preview_link(doc):
            if doc.file:
                return format_html(
                    "<a href='{}' target='_blank'>{}</a>",
                    doc.file.url,
                    os.path.basename(doc.file.name),
                )

            return ""

        def reject_link(doc):
            if doc.file:
                url = reverse(
                    "update_document_status", args=[bridge.id, doc.id, "reject"]
                )
                return format_html(" | <a href='{}'>Reject</a>", url)

            return ""

        def approve_link(doc):
            if doc.file:
                url = reverse(
                    "update_document_status", args=[bridge.id, doc.id, "approve"]
                )
                return format_html("<a href='{}'>Approve</a>", url)

            return ""

        def edit_link(doc):
            return f" | <a href='/{settings.ADMIN_URL}/{doc._meta.app_label}/{doc._meta.model_name}/{doc.id}/change/'>Edit</a>"

        rows = "".join(
            f"<tr>"
            f"<td>{doc.document_type}</td>"
            f"<td>{preview_link(doc)}</td>"
            f"<td>{DocumentStatus[doc.status].value}</td>"
            f"<td>"
            f"{approve_link(doc)}"
            f"{reject_link(doc)}"
            f"{edit_link(doc)}"
            f"</td>"
            f"</tr>"
            for doc in documents
        )

        return format_html(
            f"""
                    <table style="border-collapse: collapse; width: 100%;">
                        <thead>
                            <tr>
                                <th style="text-align: left; padding: 4px;">Document Type</th>
                                <th style="text-align: left; padding: 4px;">File</th>
                                <th style="text-align: left; padding: 4px;">Status</th>
                                <th style="text-align: left; padding: 4px;">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {rows}
                        </tbody>
                    </table>
                """
        )

    related_documents.short_description = "Documents"


@admin.register(VoiceBridgeNumber)
class VoiceBridgeNumberAdmin(UnpodCustomModelAdmin):
    list_display = (
        "id",
        "number",
        "bridge",
        "provider_credential",
        "status",
        "connectivity_type",
        "agent_id",
    )
    search_fields = ("number__number", "bridge__name", "agent")
    list_filter = ("status", "connectivity_type")


@admin.register(BridgeProviderConfig)
class BridgeProviderConfigAdmin(UnpodCustomModelAdmin):
    list_display = (
        "id",
        "name",
        "bridge",
        "provider_credential",
        "direction",
        "trunk_type",
        "numbers",
        "address",
        "sip_refer",
        "status",
    )
    search_fields = (
        "name",
        "address",
    )
    list_filter = ("direction", "trunk_type", "status")

