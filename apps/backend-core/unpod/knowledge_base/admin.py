from django.contrib import admin
from import_export.admin import ImportExportActionModelAdmin

from unpod.common.mixin import UnpodCustomModelAdmin
from unpod.knowledge_base.models import (
    DataObjectFile,
    KnowledgeBaseConfig,
    KnowledgeBaseEvals,
)


@admin.register(DataObjectFile)
class DataObjectFileAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):
    list_display = ["name", "file", "knowledge_base", "object_type", "status", "source"]
    list_filter = ["object_type", "status", "source", "knowledge_base"]
    search_fields = [
        "knowledge_base__name",
        "name",
        "token",
        "knowledge_base__description",
    ]


@admin.register(KnowledgeBaseConfig)
class KnowledgeBaseConfigAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):
    list_display = ["knowledge_base"]
    search_fields = [
        "knowledge_base__name",
        "knowledge_base__description",
        "knowledge_base__token",
        "knowledge_base__slug",
        "knowledge_base__space_organization__name",
        "knowledge_base__space_organization__domain_handle",
    ]
    list_filter = ["knowledge_base__space_organization__name"]


@admin.register(KnowledgeBaseEvals)
class KnowledgeBaseEvalsAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):
    list_display = ["eval_name", "eval_type", "linked_handle", "gen_status", "last_gen"]
    list_filter = ["gen_status", "eval_type"]
    search_fields = ["eval_name", "linked_handle"]
