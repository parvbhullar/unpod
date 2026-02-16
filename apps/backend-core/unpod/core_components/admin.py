import requests
from django.conf import settings
from django.contrib import admin
from django.db import transaction
from django.utils.safestring import mark_safe
from import_export.admin import ImportExportActionModelAdmin
from unpod.common.mixin import UnpodCustomModelAdmin
from unpod.core_components.models import (
    EventsTriggerManager,
    ModelType,
    MediaResource,
    MediaUploadRequest,
    ProfileRoles,
    Pilot,
    PilotLink,
    Plugin,
    Model,
    SampleFile,
    Tag,
    RelevantTag,
    RelevantTagLink,
    DefaultRelevantTag,
    VoiceProfiles,
    Language,
    Voice,
    GlobalSystemConfig,
    PilotTemplate,
    UseCases,
    Provider,
    TelephonyNumber,
)
from .resources import VoiceProfilesResource
from ..common.services.livekit import get_livekit_trunks
from ..common.utils import api_request
from .forms import (
    ImportPilotForm,
    UseCasesAdminForm,
    VoiceProfileAdminForm,
    PilotAdminForm,
    ProviderAdminForm,
)
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages

from ..dynamic_forms.models import DynamicFormValues, DynamicForm


# Register your models here.
# fmt: off

@admin.register(Provider)
class ProviderAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):
    form = ProviderAdminForm

    list_display = ("id", "name", "type_with_model_type", "status", "url", "form")
    search_fields = ("name", "type", "url")
    list_filter = ("type", "status")
    list_editable = ["status"]

    def type_with_model_type(self, obj):
        if obj.model_types:
            return f"{obj.type} ({', '.join(obj.model_types)})"
        return obj.type

    type_with_model_type.short_description = "Type"


@admin.register(TelephonyNumber)
class TelephonyNumberAdmin(UnpodCustomModelAdmin):
    list_display = (
        "id",
        "number",
        "provider",
        "region",
        "agent_number",
        "state",
        "active",
    )
    search_fields = ("number",)
    list_filter = ("provider", "state", "active")

    def save_model(self, request, obj, form, change):
        # Make API call to fetch phone numbers
        response = requests.get(
            f"{settings.VAPI_URL}/phone-number",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {settings.VAPI_API_KEY}",
            },
        )

        if response.status_code == 200:
            res = response.json()

            for num in res:
                if num.get("number") == obj.number:  # compare with instance field
                    # Assuming these fields exist on your model
                    obj.association = {
                        "phone_number_id": num.get("id", ""),
                        "provider": num.get("providerResourceId", ""),
                        "orgId": num.get("orgId", ""),
                        "credentialId": num.get("credentialId", ""),
                    }
                    obj.agent_number = True

        livekit_trunks = get_livekit_trunks()
        for trunk in livekit_trunks:
            # print("trubk ",trunk.get("numbers") , obj.number)
            if obj.number in trunk.get("numbers"):
                if not obj.association:
                    obj.association = {}
                obj.association["trunk_id"] = trunk.get("sip_trunk_id", "")
                obj.agent_number = True
            else:
                continue

        # Save the object as usual
        super().save_model(request, obj, form, change)


@admin.register(MediaResource)
class MediaResourceAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):
    list_display = ["media_id", "name", "file_name", "object_type", 'object_id', 'privacy_type', "size", "media_type",
                    "media_relation"]
    list_filter = ['privacy_type', 'media_type', 'object_type', 'media_relation']

    def file_name(self, obj):
        return obj.name.encode().decode("unicode-escape") if obj.name else obj.name


@admin.register(MediaUploadRequest)
class MediaUploadRequestAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):
    list_display = ["upload_id", "storage_type", "file_name", 'file_key', 'privacy_type', "status"]
    list_filter = ['storage_type', 'privacy_type', "status"]


@admin.register(ProfileRoles)
class ProfileRolesAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):
    list_display = ['role_name', 'role_code', 'parent_role', 'department']
    list_filter = ['parent_role', 'department']

from django.utils.html import format_html

@admin.register(UseCases)
class UseCasesAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):
    form = UseCasesAdminForm

    list_display = ['name', 'slug', "status", "sort_order", "svg_preview", "gradient_preview"]
    search_fields = ['name', 'slug', 'description', 'prompt', 'skills']
    list_filter = ["status"]
    list_editable = ["status", "sort_order"]

    class Media:
        css = {
            'all': ('css/gradient_picker.css', 'css/svg_icon_picker.css')
        }
        js = ('js/gradient_picker.js', 'js/svg_icon_picker.js')

    def gradient_preview(self, obj):
        if obj.background_gradient:
            return format_html(
                '<div style="width: 60px; height: 28px; background: {}; border: 1px solid #ddd; border-radius: 4px;"></div>',
                obj.background_gradient
            )
        return '-'

    gradient_preview.short_description = 'Gradient'

    def svg_preview(self, obj):
        """Show SVG icon preview in list view"""
        if obj.svg_icon:
            return format_html(
                '<div style="width: 30px; height: 30px;">{}</div>',
                mark_safe(obj.svg_icon)
            )
        return '-'

    svg_preview.short_description = 'Icon'


@admin.register(Pilot)
class PilotAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):
    form = PilotAdminForm

    list_display = ['name', 'handle', 'type', 'state', 'owner']
    list_filter = ['type', 'privacy_type', 'state']
    search_fields = ('name', 'handle', 'description', 'ai_persona', 'space__name', 'owner__name')

    change_list_template = "admin/pilots/change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("import-pilot-form/", self.admin_site.admin_view(self.pilot_import_form), name="pilot_import_form"),
        ]
        return custom_urls + urls

    def pilot_import_form(self, request):
        form = ImportPilotForm(request.POST or None)
        if request.method == "POST" and form.is_valid():
            pilot_handle = form.cleaned_data.get("pilot_handle")
            user = form.cleaned_data.get("user")
            owner = form.cleaned_data.get("organization")
            import_from = form.cleaned_data.get("import_from")
            jwt_token = form.cleaned_data.get("jwt_token")

            baseUrl = "http://127.0.0.1:8000/api/v1/"

            if import_from == "production":
                baseUrl = "https://unpod.ai/api/v1/"

            elif import_from == "qa":
                baseUrl = "https://qa1.unpod.tv/api/v1/"

            headers = {"Authorization": f"JWT {jwt_token}"}
            url = f"{baseUrl}core/pilots/{pilot_handle}/export-details/"

            data = api_request(url, 'get', headers=headers)
            pilot = data.get("data", None)

            if not pilot:
                messages.error(request, "Pilot not found in the source environment.")
            else:
                pilot.pop("domain_handle", None)
                pilot.pop("organization", None)
                pilot.pop("space", None)
                pilot.pop("voice_profile", None)
                pilot.pop("plugins", [])
                pilot.pop("knowledge_bases", [])
                pilot.pop("kb_list", [])
                pilot.pop("users", [])
                pilot.pop("user_role", None)
                pilot.pop("conversations_count", 0)

                tags = pilot.pop("tags", [])
                chat_model = pilot.pop("chat_model", None)
                embedding_model = pilot.pop("embedding_model", None)
                components = pilot.pop("components", None)
                blocks = pilot.pop("blocks", [])

                with transaction.atomic():
                    try:
                        agent, created = Pilot.objects.get_or_create(
                            handle=pilot.get("handle"),
                            # created_by=user.id,
                            defaults={
                                **pilot,
                                'owner_id': owner.id,
                                "created_by": user.id,
                                "updated_by": user.id,
                            }
                        )

                        if created:
                            # Handle chat_model
                            if chat_model:
                                model_obj = Model.objects.filter(slug=chat_model.get("slug")).first()
                                if model_obj:
                                    agent.llm_model = model_obj

                            # Handle embedding_model
                            if embedding_model:
                                model_obj = Model.objects.filter(slug=embedding_model.get("slug")).first()
                                if model_obj:
                                    agent.embedding_model = model_obj

                            # Handle tags
                            for tag_name in tags:
                                tag_obj, _ = Tag.objects.get_or_create(name=tag_name)
                                agent.tags.add(tag_obj)

                            # Handle blocks
                            # for block in blocks:
                            #     block.pop("id", None)
                            #     block['superbook'] = agent
                            #     block['created_by'] = user.id
                            #     block['updated_by'] = user.id
                            #     Block.objects.create(**block)

                            # Handle components
                            if components:
                                for group, forms in components.items():
                                    for form in forms:
                                        form_values = form.get("form_values", {})
                                        if form_values:
                                            slug = form.get("slug")
                                            form_exists = DynamicForm.objects.filter(slug=slug).first()
                                            if form_exists is None:
                                                continue

                                            form_values.pop("id", None)
                                            form_values['parent_id'] = agent.handle
                                            form_values['created_by'] = user
                                            form_values['form'] = form_exists
                                            DynamicFormValues.objects.create(**form_values)

                            agent.save()
                            messages.success(request, "Pilot imported successfully!")
                            return redirect("admin:pilot_import_form")

                        else:
                            messages.info(request, "Pilot with this handle already exists.")
                    except Exception as e:
                        messages.error(request, f"An error occurred during import: {str(e)}")

        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,  # 🟢 required for breadcrumbs
            "title": "Import Pilot",
            "form": form,
        }
        return render(request, "admin/pilots/pilot_import_form.html", context)


@admin.register(PilotLink)
class PilotLinkAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):
    list_display = ['pilot', 'content_type']
    list_filter = ['content_type']
    search_fields = ('pilot__name',)


@admin.register(Plugin)
class PluginAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):
    list_display = ['name', 'slug', 'type']
    list_filter = ['type', 'privacy_type']
    search_fields = ('name', 'description', 'owner__name')


@admin.register(Voice)
class VoiceAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):
    list_display = ('name', 'code', 'provider', 'latency', 'cost', 'get_languages', 'status', 'slug')
    list_filter = ('status',)
    search_fields = ('name', 'code')
    list_editable = ['status']  # editable directly in list

    def get_languages(self, obj):
        return ", ".join([lang.name for lang in obj.language.all()])

    get_languages.short_description = "Languages"

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "provider":
            kwargs["queryset"] = Provider.objects.filter(status='active')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Language)
class LanguageAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ['name']


@admin.register(ModelType)
class ModelTypeAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):
    list_display = ['name', 'code']
    search_fields = ['name', 'code']
    ordering = ['name']


@admin.register(Model)
class ModelAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):
    list_display = [
        'name',
        "status",
        'provider',
        'get_model_types',
        'get_languages',
        'get_voice',
        'slug',
        'codename',
        "token_limit",
        "cost",
        "tool_calling",
        "description",
        "sort_order"
    ]
    list_filter = ['provider', 'model_types', 'tool_calling', "status", "inference", "realtime_sts"]
    search_fields = ['languages__name', 'voice__name', 'name', 'model_types__name', "provider__name", "description", "cost"]
    list_editable = ["status", "sort_order", "cost"]  # editable directly in list

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "languages":
            kwargs["queryset"] = Language.objects.filter(status=True)
        if db_field.name == "voice":
            kwargs["queryset"] = Voice.objects.filter(status=True)

        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "languages":
            kwargs["queryset"] = Language.objects.filter(status=True)
        if db_field.name == "voice":
            kwargs["queryset"] = Voice.objects.filter(status=True)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_model_types(self, obj):
        return ", ".join([t.name for t in obj.model_types.all()])

    get_model_types.short_description = "Model Types"

    def get_languages(self, obj):
        return ", ".join([lang.name for lang in obj.languages.all()])

    get_languages.short_description = "Languages"

    def get_voice(self, obj):
        return ", ".join([v.name for v in obj.voice.all()])

    get_voice.short_description = "Voice"


@admin.register(Tag)
class ModelAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):
    list_display = ['name', 'slug', ]


@admin.register(EventsTriggerManager)
class BlockAdmin(ImportExportActionModelAdmin):
    list_display = ["event_name", "event_type", "event_execution", "status", "created"]
    list_filter = ["event_name", "event_type", "event_execution", "status"]


@admin.register(RelevantTag)
class RelevantTagAdmin(ImportExportActionModelAdmin):
    list_display = ('name', 'slug', 'is_default')
    search_fields = ('name', 'slug')
    list_filter = ('is_default',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(RelevantTagLink)
class RelevantTagLinkAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):
    list_display = ('tag', 'content_type', 'object_id', 'type', 'sort_order')
    list_filter = ('type', 'content_type')
    search_fields = ('tag__name', 'object_id')
    raw_id_fields = ('tag',)


@admin.register(DefaultRelevantTag)
class DefaultRelevantTagAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):
    list_display = ('tag', 'content_type', 'space_content_type', 'sort_order')
    search_fields = ('tag__name',)
    list_filter = ('content_type',)


@admin.register(VoiceProfiles)
class VoiceProfilesAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):
    form = VoiceProfileAdminForm
    resource_class = VoiceProfilesResource

    list_display = (
        'agent_profile_id',
        'name',
        'quality',
        'gender',
        'status',
        'sort_order',
        'llm_model',
        'get_tts_languages'
    )
    search_fields = ("name", "description", "temperature", "tts_provider__name", "tts_voice__name", "tts_model__name")
    list_filter = ('quality', "status", 'estimated_cost')
    list_editable = ["status", "sort_order"]

    def get_tts_languages(self, obj):
        return ", ".join([lang.name for lang in obj.tts_language.all()])

    get_tts_languages.short_description = 'TTS Languages'


@admin.register(GlobalSystemConfig)
class GlobalSystemConfigAdmin(ImportExportActionModelAdmin):
    list_display = ('key', 'value')


@admin.register(PilotTemplate)
class PilotTemplateAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):
    list_display = ('name', 'slug', 'category', 'is_active', 'display_order', 'use_count', 'created')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'handle', 'description')
    ordering = ('display_order', '-created')
    readonly_fields = ('use_count', 'created', 'modified')

    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'slug', 'category', 'description', 'thumbnail')
        }),
        ('Template Content', {
            'fields': ('system_prompt', 'ai_persona', 'greeting_message'),
            'classes': ('collapse',)
        }),
        ('Configuration', {
            'fields': ('knowledge_base_schema', 'config', 'telephony_config'),
            'classes': ('collapse',)
        }),
        ('Settings', {
            'fields': ('is_active', 'display_order', 'use_count')
        }),
        ('Timestamps', {
            'fields': ('created', 'modified'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SampleFile)
class SampleFileAdmin(ImportExportActionModelAdmin, admin.ModelAdmin):
    list_display = ['file_name', 'file_slug', "file_type", "file_size"]
    search_fields = ['file_name', 'file_slug']
    list_filter = ["file_type"]
