from django.contrib import admin
from .models import Document
from ..common.mixin import UnpodCustomModelAdmin


@admin.register(Document)
class DocumentAdmin(UnpodCustomModelAdmin):
    list_display = ('id', 'module_type', 'document_type', 'status', 'user_id', 'organization', 'uploaded_at')
    search_fields = ('module_type', 'document_type', 'other_document_name', 'version')
    list_filter = ('document_type', 'uploaded_at')
