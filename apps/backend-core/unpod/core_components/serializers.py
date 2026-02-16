import os
from collections import defaultdict
from urllib.parse import unquote

from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.utils.text import slugify
from rest_framework import serializers
from unpod.common.decorators import checkUserReturnDefault
from unpod.common.enum import (
    FileStorage,
    MediaPrivacyType,
    MediaUploadStatus,
    SpaceType,
    ModelTypes,
    RoleCodes,
)
from unpod.common.exception import APIException206
from unpod.common.file import getFileType, getS3FileURLFromURL
from unpod.common.geo import getIPAddressLocation, getUserIp
from unpod.common.s3 import generate_presigned_url_post
from unpod.common.string import get_random_string
from unpod.common.uuid import generate_uuid
from unpod.core_components.models import (
    MediaResource,
    MediaUploadRequest,
    Pilot,
    Plugin,
    PilotLink,
    Model,
    Tag,
    RelevantTag,
    VoiceProfiles,
    GlobalSystemConfig,
    PilotTemplate,
    UseCases,
    Provider,
    TelephonyNumber,
)
from unpod.common.storage_backends import cloudinaryBackend, imagekitBackend, muxBackend
from unpod.dynamic_forms.models import DynamicForm, FormFields, DynamicFormValues
from unpod.dynamic_forms.serializers import (
    DynamicFormFieldSerializer,
    DynamicFormValuesSerializer,
)
from unpod.roles.constants import DEFAULT_PILOT_PERMISSION_ROLE
from unpod.space.models import SpaceOrganization, Space
from unpod.space.serializers import SpaceOrganizationSerializers
from unpod.thread.models import ThreadPost
from unpod.users.models import User


# fmt: off

class ProviderSerializer(serializers.ModelSerializer):
    icon = serializers.SerializerMethodField()
    form_slug = serializers.CharField(source="form.slug", read_only=True)

    class Meta:
        model = Provider
        fields = [
            "id",
            "name",
            "type",
            "model_types",
            "url",
            "description",
            "icon",
            "form_slug",
            "status",
        ]

    def get_icon(self, obj):
        if obj.icon:
            return imagekitBackend.generateURL(obj.icon.name)
        return None


class TelephonyNumberSerializer(serializers.ModelSerializer):
    provider = serializers.PrimaryKeyRelatedField(
        queryset=Provider.objects.all(), write_only=True
    )
    provider_details = ProviderSerializer(source="provider", read_only=True)

    class Meta:
        model = TelephonyNumber
        fields = [
            "id",
            "number",
            "provider",
            "provider_details",
            "country_code",
            "region",
            "state",
            "active",
            "owner_type",
            "number_type",
            "association",
            "agent_number",
        ]


class MediaListSerializer(serializers.ModelSerializer):
    media_url = serializers.SerializerMethodField()

    class Meta:
        model = MediaResource
        fields = [
            "object_type",
            "object_id",
            "size",
            "media_id",
            "media_type",
            "media_relation",
            "name",
            "media_url",
            "url",
            "sequence_number",
        ]

    def get_media_url(self, obj):
        if obj.storage_type == FileStorage.s3.name:
            if obj.media_type == "image":
                return imagekitBackend.generateURL(obj.file_storage_url.name)
            if obj.privacy_type == MediaPrivacyType.private.name:
                return obj.file_storage_url.url
            return obj.url
        elif obj.storage_type == FileStorage.cloudinary.name:
            if obj.public_id:
                obj_type = obj.privacy_type
                if obj_type == "public":
                    obj_type = "upload"
                cloudObject = cloudinaryBackend.getMediaData(obj.public_id, obj_type)
                return cloudObject.get("url")
        return obj.url


class MediaUploadSerializer(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True, required=True)

    class Meta:
        model = MediaResource
        fields = ["object_type", "object_id", "file", "media_relation"]

    def upload(self, validated_data, return_dict=False):
        request = self.context.get("request")
        file = validated_data.pop("file")
        loc_data = getIPAddressLocation(getUserIp(request))
        print("Loc Data", loc_data)
        validated_data["lat"] = loc_data.get("lat")
        validated_data["lng"] = loc_data.get("lng")
        validated_data["size"] = file.size
        validated_data["created_by"] = request.user.id
        validated_data["updated_by"] = request.user.id
        validated_data["media_id"] = generate_uuid()
        validated_data["media_type"] = getFileType(file.name)
        validated_data["storage_type"] = FileStorage.s3.name
        if not validated_data.get("object_id"):
            validated_data["media_status"] = MediaUploadStatus.created.name
        if (
            "media_relation" not in validated_data
            or validated_data.get("media_relation", "") == ""
        ):
            validated_data["media_relation"] = "media"
        validated_data["name"] = file.name
        if validated_data["media_type"] in ["video"]:
            cloudObject = cloudinaryBackend.processFileUpload(
                file, validated_data["media_type"], file.size
            )
            validated_data["public_id"] = cloudObject.get("public_id")
            validated_data["url"] = cloudObject.get("url")
            validated_data["storage_type"] = FileStorage.cloudinary.name
            validated_data["privacy_type"] = "public"
        else:
            validated_data["file_storage_url"] = file
        # validated_data['name'] = emoji.replace_emoji(validated_data['name'])
        validated_data["name"] = (
            validated_data["name"].encode("unicode-escape").decode()
        )
        instance = self.create(validated_data)
        if instance.file_storage_url:
            file_url = getS3FileURLFromURL(instance.file_storage_url.url)
            instance.updateModel({"url": file_url})
        if return_dict:
            if instance.file_storage_url:
                validated_data["media_url"] = instance.file_storage_url.url
                validated_data.pop("file_storage_url", "")
                validated_data["url"] = file_url
            elif instance.public_id:
                validated_data["media_url"] = instance.url
            return validated_data
        return instance


class MediaUploadMutlipleSerializer(serializers.ModelSerializer):
    files = serializers.ListField(
        child=serializers.FileField(write_only=True, required=True),
        write_only=True,
        required=True,
    )

    class Meta:
        model = MediaResource
        fields = ["object_type", "object_id", "files"]

    def upload(self, validated_data):
        final_data = []
        common_data = {}
        request = self.context.get("request")
        files = validated_data.pop("files")
        loc_data = getIPAddressLocation(getUserIp(request))
        common_data["lat"] = loc_data.get("lat")
        common_data["lng"] = loc_data.get("lng")
        common_data["created_by"] = request.user.id
        common_data["updated_by"] = request.user.id
        common_data["storage_type"] = FileStorage.s3.name
        if not validated_data.get("object_id"):
            common_data["media_status"] = MediaUploadStatus.created.name
        else:
            common_data["object_id"] = validated_data["object_id"]
        common_data["media_relation"] = "attachment"

        for file in files:
            file_data = {}
            file_data["size"] = file.size
            file_data["file_storage_url"] = file
            file_data["media_type"] = getFileType(file.name)
            file_data["media_id"] = generate_uuid()
            file_data["name"] = file.name.encode("unicode-escape").decode()
            file_data.update(common_data)
            final_data.append(MediaResource(**file_data))
        instance_list = self.Meta.model.objects.bulk_create(final_data)
        for instance in instance_list:
            file_url = getS3FileURLFromURL(instance.file_storage_url.url)
            self.Meta.model.objects.filter(media_id=instance.media_id).update(
                url=file_url
            )
            instance.url = file_url
        return instance_list


class MediaDataUploadSerializer(serializers.ModelSerializer):
    media_data = serializers.JSONField(write_only=True, required=True)

    class Meta:
        model = MediaResource
        fields = ["object_type", "object_id", "media_relation", "media_data"]

    def upload_media(self, validated_data, return_dict=False):
        request = self.context.get("request")
        media_data = validated_data.pop("media_data")
        # upload_id = media_data['upload_id']
        asset_id = media_data["asset_id"]
        loc_data = getIPAddressLocation(getUserIp(request))
        validated_data["lat"] = loc_data.get("lat")
        validated_data["lng"] = loc_data.get("lng")
        validated_data["created_by"] = request.user.id
        validated_data["updated_by"] = request.user.id
        validated_data["media_id"] = generate_uuid()
        validated_data["media_type"] = getFileType(media_data["file_name"])
        validated_data["size"] = media_data["size"]
        validated_data["media_metadata"] = media_data.get("media_metadata", {})
        if (
            "media_relation" not in validated_data
            or validated_data.get("media_relation", "") == ""
        ):
            validated_data["media_relation"] = "media"
        validated_data["name"] = media_data["file_name"]
        validated_data["public_id"] = asset_id
        validated_data["storage_type"] = FileStorage.mux.name
        validated_data["storage_data"] = media_data["storage_data"]
        # validated_data['name'] = emoji.replace_emoji(validated_data['name'])
        validated_data["name"] = (
            validated_data["name"].encode("unicode-escape").decode()
        )
        instance = self.create(validated_data)
        return instance

    def upload_media_custom(self, validated_data):
        user = self.context.get("user")
        media_data = validated_data.pop("media_data")
        asset_id = media_data["asset_id"]
        loc_data = {}
        validated_data["lat"] = loc_data.get("lat", "00")
        validated_data["lng"] = loc_data.get("lng", "00")
        validated_data["created_by"] = user.id
        validated_data["updated_by"] = user.id
        validated_data["media_id"] = generate_uuid()
        validated_data["media_type"] = getFileType(media_data["file_name"])
        validated_data["size"] = media_data["size"]
        validated_data["media_metadata"] = media_data.get("media_metadata", {})
        if (
            "media_relation" not in validated_data
            or validated_data.get("media_relation", "") == ""
        ):
            validated_data["media_relation"] = "media"
        validated_data["name"] = media_data["file_name"]
        validated_data["public_id"] = asset_id
        validated_data["storage_type"] = FileStorage.mux.name
        validated_data["storage_data"] = media_data
        # validated_data['name'] = emoji.replace_emoji(validated_data['name'])
        validated_data["name"] = (
            validated_data["name"].encode("unicode-escape").decode()
        )
        instance = self.create(validated_data)
        return instance


class MediaUploadRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaUploadRequest
        fields = ["file_name"]

    def create(self, validated_data):
        request = self.context.get("request")
        file_name, file_extension = os.path.splitext(validated_data["file_name"])
        file_name = f"media/upload/{file_name}_"
        file_key = get_random_string(file_name, length=8)
        file_key = f"{file_key}{file_extension}"
        validated_data["file_key"] = file_key
        validated_data["storage_type"] = FileStorage.s3.name
        validated_data["created_by"] = request.user.id
        validated_data["updated_by"] = request.user.id
        validated_data["upload_id"] = generate_uuid()
        storage_response = generate_presigned_url_post(file_key)
        validated_data["storage_response"] = storage_response
        # validated_data['file_name'] = emoji.replace_emoji(validated_data['file_name'])
        validated_data["file_name"] = (
            validated_data["file_name"].encode("unicode-escape").decode()
        )
        instance = self.Meta.model.objects.create(**validated_data)
        return instance


class MediaUploadRequestDetailSerializer(serializers.ModelSerializer):
    signed_url = serializers.ReadOnlyField(source="storage_response.url")
    signed_fields = serializers.ReadOnlyField(source="storage_response.fields")

    class Meta:
        model = MediaUploadRequest
        fields = ["upload_id", "signed_url", "signed_fields"]


class MessagingBlockList(serializers.Serializer):
    thread_id = serializers.CharField(max_length=255, read_only=True)
    block_id = serializers.CharField(max_length=255, read_only=True)
    user_id = serializers.CharField(max_length=255, read_only=True)
    user = serializers.JSONField(read_only=True)
    block = serializers.CharField(max_length=255, read_only=True)
    block_type = serializers.CharField(max_length=255, read_only=True)
    data = serializers.JSONField(read_only=True)
    media = serializers.SerializerMethodField(read_only=True)
    seq_number = serializers.IntegerField(read_only=True)
    reaction_count = serializers.IntegerField(read_only=True)
    parent_id = serializers.CharField(max_length=255, read_only=True)
    parent = serializers.JSONField(read_only=True)
    created = serializers.CharField(read_only=True)

    def get_media(self, obj):
        if obj.get("block_type") != "video_msg":
            return {}
        public_id = obj.get("data", {}).get("public_id")
        media_data = {}
        if public_id:
            playback_data = muxBackend.getPlaybackId(public_id)
            if "id" in playback_data:
                media_data["playback_id"] = playback_data["id"]
                storage_data = obj.get("data", {}).get("storage_data", {})
                data = obj.get("data", {})
                media_data.update(
                    {
                        "name": storage_data["file_name"],
                        "media_type": data["media_type"],
                        "media_relation": "content",
                        "size": 13927646,
                        "media_id": data["media_id"],
                    }
                )
                return media_data
        return {}


class PilotFullSerializer(serializers.ModelSerializer):
    """
    Tier 3: Complete serializer with all fields including heavy computed data.

    Use this for:
    - Full API exports
    - Complete pilot configuration retrieval
    - Admin/management interfaces needing all data

    Performance: ~30+ queries for single pilot (use sparingly!)

    Note: This is the same as the original PilotRetrieveSerializer.
    Consider using PilotDetailSerializer instead unless you need ALL fields.
    """
    chat_model = serializers.SerializerMethodField()
    embedding_model = serializers.SerializerMethodField()
    plugins = serializers.SerializerMethodField()
    knowledge_bases = serializers.SerializerMethodField()
    hub_domain_handle = serializers.SerializerMethodField()
    logo = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    numbers = serializers.SerializerMethodField()
    kb_list = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()
    users = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()
    conversations_count = serializers.SerializerMethodField()
    space = serializers.SerializerMethodField()
    voice_profile = serializers.SerializerMethodField()
    components = serializers.SerializerMethodField()
    template = serializers.CharField(source="template.slug", read_only=True)
    eval_kn_bases = serializers.SerializerMethodField()
    eval_knowledge_bases = serializers.SerializerMethodField()

    class Meta:
        model = Pilot
        fields = (
            "name",
            "handle",
            "privacy_type",
            "type",
            "logo",
            "ai_persona",
            "chat_model",
            "embedding_model",
            "config",
            "plugins",
            "knowledge_bases",
            "state",
            "hub_domain_handle",
            "ai_persona_config",
            "response_prompt",
            "allow_user_to_change",
            "description",
            "tags",
            "kb_list",
            "organization",
            "users",
            "user_role",
            "conversations_count",
            "reaction_count",
            "created_by",
            "questions",
            "greeting_message",
            "system_prompt",
            "token",
            "telephony_enabled",
            "workflow_enabled",
            "telephony_config",
            "numbers",
            "space",
            "temperature",
            "voice_profile",
            "enable_memory",
            "enable_followup",
            "followup_prompt",
            "enable_callback",
            "notify_via_sms",
            "enable_handover",
            "instant_handover",
            "handover_number_cc",
            "handover_number",
            "handover_person_name",
            "handover_person_role",
            "handover_prompt",
            "region",
            "calling_days",
            "calling_time_ranges",
            "number_of_words",
            "voice_seconds",
            "back_off_seconds",
            "voice_temperature",
            "voice_speed",
            "voice_prompt",
            "purpose",
            "template",
            "conversation_tone",
            "realtime_evals",
            "eval_kn_bases",
            "eval_knowledge_bases",
            "components",
        )

    def get_components(self, obj):
        forms = DynamicForm.objects.filter(type="component", parent_type="agent", status="active")
        components = defaultdict(list)
        for form in forms:
            fields = FormFields.objects.filter(form=form, status="active")
            form_values = DynamicFormValues.objects.filter(form=form, parent_type="agent", parent_id=obj.handle).first()

            form_data = {
                "id": form.id,
                "name": form.name,
                "slug": form.slug,
                "description": form.description,
                "form_fields": DynamicFormFieldSerializer(fields, many=True).data,
                "form_values": DynamicFormValuesSerializer(form_values, many=False).data if form_values else None,
            }

            if form.group_key:
                components[form.group_key].append(form_data)
            else:
                components["default"].append(form_data)

        return components


    def get_voice_profile(self, obj):
        if isinstance(obj, Pilot) and isinstance(obj.telephony_config, dict) and obj.telephony_config.get("voice_profile_id"):
            voice_profile = VoiceProfiles.objects.filter(pk=obj.telephony_config.get("voice_profile_id")).first()
            if voice_profile:
                return VoiceProfilesSerializer(voice_profile).data
            return {}

    def get_chat_model(self, obj):
        return (
            {
                "name": obj.llm_model.name,
                "codename": obj.llm_model.codename,
                "provider_info": ProviderSerializer(obj.llm_model.provider).data if obj.llm_model.provider else None
            }
            if hasattr(obj, "llm_model") and obj.llm_model
            else {}
        )

    def get_embedding_model(self, obj):
        return (
            {
                "name": obj.embedding_model.name,
                "codename": obj.embedding_model.codename,
            }
            if hasattr(obj, "embedding_model") and obj.embedding_model
            else {}
        )

    def get_plugins(self, obj):
        return list(
            Plugin.objects.filter(pilots__pilot__id=obj.id).values_list(
                "slug", flat=True
            )
        )

    def get_knowledge_bases(self, obj):
        return list(
            Space.objects.filter(
                pilots__pilot__id=obj.id, space_type=SpaceType.knowledge_base.name
            ).values_list("slug", flat=True)
        )

    def get_hub_domain_handle(self, obj):
        return obj.owner.domain_handle if obj.owner else ""

    def get_logo(self, obj):
        if obj.logo:
            return imagekitBackend.generateURL(obj.logo.name)
        return None

    def get_tags(self, obj):
        return list(obj.tags.values_list("name", flat=True))

    def get_numbers(self, obj):
        return TelephonyNumberSerializer(obj.numbers.all(), many=True).data

    def get_kb_list(self, obj):
        return list(
            Space.objects.filter(
                pilots__pilot__id=obj.id, space_type=SpaceType.knowledge_base.name
            ).values("name", "slug", "token")
        )

    def get_eval_kn_bases(self, obj):
        return list(
            obj.eval_kn_bases.all().values_list("slug", flat=True)
        )

    def get_eval_knowledge_bases(self, obj):
        return list(
            obj.eval_kn_bases.all().values("name", "slug", "token")
        )

    def get_organization(self, obj):
        if hasattr(obj, "owner"):
            return SpaceOrganizationSerializers(obj.owner).data
        return {}

    @checkUserReturnDefault([])
    def get_users(self, obj):
        return PilotPermissionSerializer(
            obj.link_qs.filter(content_type=ContentType.objects.get_for_model(User)),
            many=True,
        ).data

    @checkUserReturnDefault(DEFAULT_PILOT_PERMISSION_ROLE)
    def get_user_role(self, obj):
        request = self.context.get("request")
        link = obj.link_qs.filter(
            content_type=ContentType.objects.get_for_model(User),
            object_id=request.user.id,
        ).first()
        if link:
            return link.role_code()
        return ""

    def get_conversations_count(self, obj):
        return ThreadPost.objects.filter(related_data__pilot=obj.handle).count()

    def get_space(self, obj):
        if obj.space:
            return {
                "id": obj.space.id,
                "name": obj.space.name,
                "slug": obj.space.slug,
                "description": obj.space.description
            }
        return None


class PilotExportSerializer(PilotFullSerializer):
    blocks = serializers.SerializerMethodField()

    class Meta(PilotFullSerializer.Meta):
        fields = PilotFullSerializer.Meta.fields + ("blocks",)

    # def get_blocks(self, obj):
    #     blocks = Block.objects.filter(superbook=obj).order_by('seq_order')
    #     return BlockSerializer(blocks, many=True).data


class PilotMenusSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()

    class Meta:
        model = Pilot
        fields = (
            "name",
            "handle",
            "description",
            "privacy_type",
            "type",
            "logo",
            "state",
        )

    def get_logo(self, obj):
        if obj.logo:
            return imagekitBackend.generateURL(obj.logo.name)
        return None


class PilotListSerializer(PilotMenusSerializer):
    knowledge_bases = serializers.SerializerMethodField()
    hub_domain_handle = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    kb_list = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()
    template = serializers.CharField(source="template.slug", read_only=True)
    space = serializers.SerializerMethodField()

    class Meta(PilotMenusSerializer.Meta):
        fields = PilotMenusSerializer.Meta.fields + (
            "created_by",
            "ai_persona",
            "config",
            "knowledge_bases",
            "hub_domain_handle",
            "ai_persona_config",
            "response_prompt",
            "allow_user_to_change",
            "tags",
            "kb_list",
            "organization",
            "reaction_count",
            "created_by",
            "questions",
            "calling_days",
            "calling_time_ranges",
            "number_of_words",
            "voice_seconds",
            "back_off_seconds",
            "voice_temperature",
            "voice_speed",
            "purpose",
            "template",
            "conversation_tone",
            "space"
        )

    def get_knowledge_bases(self, obj):
        return list(
            Space.objects.filter(
                pilots__pilot__id=obj.id, space_type=SpaceType.knowledge_base.name
            ).values_list("slug", flat=True)
        )

    def get_hub_domain_handle(self, obj):
        return obj.owner.domain_handle if obj.owner else ""

    def get_tags(self, obj):
        return list(obj.tags.values_list("name", flat=True))

    def get_kb_list(self, obj):
        return list(
            Space.objects.filter(
                pilots__pilot__id=obj.id, space_type=SpaceType.knowledge_base.name
            ).values("name", "slug")
        )

    def get_organization(self, obj):
        if hasattr(obj, "owner"):
            return SpaceOrganizationSerializers(obj.owner).data
        return {}

    def get_space(self, obj):
        if obj.space:
            return {
                "id": obj.space.id,
                "name": obj.space.name,
                "slug": obj.space.slug,
                "description": obj.space.description
            }
        return None


class ModelSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    logo = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    provider_info = ProviderSerializer(source='provider', read_only=True)
    languages = serializers.SerializerMethodField()
    voices = serializers.SerializerMethodField()

    class Meta:
        model = Model
        fields = (
            "id", "name", "slug", "codename", "logo", "description", "token_limit", "provider", "provider_info", "tags", "config",
            "languages", "voices", "realtime_sts", "inference", "status")

    def get_tags(self, obj):
        return list(obj.tags.values_list("name", flat=True))

    def get_logo(self, obj):
        if obj.logo:
            return imagekitBackend.generateURL(obj.logo.name)
        return None

    def get_languages(self, obj):
        return [
            {"id": lang.id, "name": lang.name, "code": lang.code}
            for lang in obj.languages.all()
        ]

    def get_voices(self, obj):
        return [
            {"id": voice.id, "name": voice.name, "code": voice.code}
            for voice in obj.voice.filter(status=True)
        ]


class PluginSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()

    class Meta:
        model = Plugin
        fields = (
            "name",
            "slug",
            "logo",
            "description",
        )

    def get_logo(self, obj):
        if obj.logo:
            return imagekitBackend.generateURL(obj.logo.name)
        return None


class KBSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()

    class Meta:
        model = Space
        fields = (
            "name",
            "slug",
            "logo",
            "description",
        )

    def get_logo(self, obj):
        if obj.logo:
            return imagekitBackend.generateURL(obj.logo.name)
        return None


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("name",)


class PilotPermissionSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=False,
    )
    role_code = serializers.ChoiceField(
        choices=[RoleCodes.viewer.name, RoleCodes.editor.name], required=True
    )
    invite_by = serializers.CharField(read_only=True)
    full_name = serializers.CharField(read_only=True)
    slug = serializers.CharField(read_only=True)

    class Meta:
        model = PilotLink
        fields = (
            "email",
            "role_code",
            "invite_by",
            "full_name",
            "slug",
        )

    def create(self, validated_data):
        if not validated_data.get("email"):
            raise APIException206(detail={"message": "Email is required"})
        request = self.context.get("request")
        pilot = self.context.get("pilot")
        user = User.objects.filter(email=validated_data["email"]).first()
        if user is None:
            raise APIException206(detail={"message": "User Not Found"})
        if PilotLink.objects.filter(pilot=pilot, users=user).exists():
            raise APIException206(detail={"message": "Pilot Already Shared with User"})
        pilot_link = PilotLink.objects.create(
            pilot=pilot,
            content_object=user,
            created_by=request.user.id,
            link_config={
                "role_code": validated_data["role_code"],
            },
        )
        return pilot_link

    def update(self, pilot_link, validated_data):
        pilot_link.link_config = {
            "role_code": validated_data["role_code"],
        }
        pilot_link.save()
        return pilot_link


class CoreInviteRequestPublic(serializers.Serializer):
    email = serializers.EmailField(required=True)
    invite_type = serializers.ChoiceField(
        choices=["space", "organization"], default="space"
    )
    slug = serializers.CharField(required=True)

    def validate(self, attrs):
        from unpod.thread.models import ThreadPost
        invite_type = attrs.get("invite_type")
        slug = attrs.get("slug")
        if invite_type == "space":
            obj = Space.objects.filter(slug=slug, space_type="general").first()
        elif invite_type == "post":
            obj = ThreadPost.objects.filter(slug=slug).first()
        elif invite_type == "organization":
            obj = SpaceOrganization.objects.filter(domain_handle=slug).first()
        else:
            raise APIException206(detail={"message": "Invalid invite type"})
        if not obj:
            raise APIException206(detail={"message": "Invalid slug"})
        attrs["invite_obj"] = obj
        return attrs


class RelevantTagSerializer(serializers.ModelSerializer):
    description = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = RelevantTag
        fields = ('name', 'slug', 'description')


class PilotSerializer(serializers.ModelSerializer):
    chat_model = serializers.JSONField(required=False)
    embedding_model = serializers.JSONField(required=False)
    plugins = serializers.ListField(child=serializers.CharField(), required=False)
    knowledge_bases = serializers.ListField(
        child=serializers.CharField(), required=False
    )
    eval_kn_bases = serializers.ListField(child=serializers.CharField(), required=False)
    tags = serializers.ListField(child=serializers.CharField(), required=False)
    user_list = serializers.JSONField(required=False)
    space_slug = serializers.CharField(required=False)
    template = serializers.CharField(required=False)
    questions = serializers.ListField(
        child=serializers.CharField(), required=False, allow_null=True, default=[]
    )
    components = serializers.JSONField(required=False)

    class Meta:
        model = Pilot
        fields = (
            "name",
            "handle",
            "privacy_type",
            "type",
            "logo",
            "ai_persona",
            "chat_model",
            "embedding_model",
            "config",
            "plugins",
            "knowledge_bases",
            "state",
            "description",
            "tags",
            "user_list",
            "ai_persona_config",
            "response_prompt",
            "allow_user_to_change",
            "questions",
            "greeting_message",
            "system_prompt",
            "token",
            "telephony_enabled",
            "workflow_enabled",
            "telephony_config",
            "space_slug",
            "temperature",
            "enable_memory",
            "enable_followup",
            "followup_prompt",
            "enable_callback",
            "notify_via_sms",
            "enable_handover",
            "instant_handover",
            "handover_number_cc",
            "handover_number",
            "handover_person_name",
            "handover_person_role",
            "handover_prompt",
            "region",
            "calling_days",
            "calling_time_ranges",
            "number_of_words",
            "voice_seconds",
            "back_off_seconds",
            "voice_temperature",
            "voice_speed",
            "voice_prompt",
            "purpose",
            "conversation_tone",
            "realtime_evals",
            "eval_kn_bases",
            "template",
            "components",
        )
        extra_kwargs = {
            "name": {"required": True},
            "logo": {"required": False},
            "handle": {"required": True},
            "privacy_type": {"required": False},
            "state": {"required": False},
            "ai_persona": {"required": False},
            "config": {"required": False},
            "ai_persona_config": {"required": False},
            "response_prompt": {"required": False},
            "allow_user_to_change": {"required": False},
            "greeting_message": {"required": False},
            "system_prompt": {"required": False},
            "token": {"required": False},
            "telephony_enabled": {"required": False},
            "workflow_enabled": {"required": False},
            "telephony_config": {"required": False},
            "space_slug": {"required": False},
            "temperature": {"required": False},
            "enable_memory": {"required": False},
            "enable_followup": {"required": False},
            "followup_prompt": {"required": False},
            "enable_callback": {"required": False},
            "notify_via_sms": {"required": False},
            "enable_handover": {"required": False},
            "instant_handover": {"required": False},
            "handover_number_cc": {"required": False},
            "handover_number": {"required": False},
            "handover_person_name": {"required": False},
            "handover_person_role": {"required": False},
            "handover_prompt": {"required": False},
            "region": {"required": False},
            "calling_days": {"required": False},
            "calling_time_ranges": {"required": False},
            "number_of_words": {"required": False},
            "voice_seconds": {"required": False},
            "back_off_seconds": {"required": False},
            "voice_temperature": {"required": False},
            "voice_speed": {"required": False},
            "voice_prompt": {"required": False},
            "purpose": {"required": False},
            "conversation_tone": {"required": False},
            "realtime_evals": {"required": False},
            "eval_kn_bases": {"required": False},
            "template": {"required": False},
            "components": {"required": False},
        }

    def validate_handle(self, value):
        # URL decode the handle (converts %C3%A9 to é)
        decoded_value = unquote(value)

        # Slugify to remove special characters and convert to ASCII
        # This also lowercases the value and replaces spaces with hyphens
        sanitized_value = slugify(decoded_value, allow_unicode=False)

        if not sanitized_value:
            raise serializers.ValidationError(
                "Handle must contain at least some alphanumeric characters"
            )

        # For updates, exclude the current instance when checking for duplicates
        if self.instance:
            if Pilot.objects.filter(handle=sanitized_value).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError("Pilot handle is already taken")
        # For creates, just check if the handle exists
        elif Pilot.objects.filter(handle=sanitized_value).exists():
            raise serializers.ValidationError("Pilot handle is already taken")

        return sanitized_value

    def validate_telephony_config(self, value):
        # Skip validation if empty
        if not value:
            return value

        # Only validate keys that are present (allow partial updates)

        # Validate transcriber configuration if present
        if "transcriber" in value:
            transcriber = value.get("transcriber", {})
            if not isinstance(transcriber, dict):
                raise serializers.ValidationError("transcriber must be an object")

            transcriber_keys = ["provider", "language", "model"]
            for key in transcriber_keys:
                if key not in transcriber:
                    raise serializers.ValidationError(
                        f"Missing required key in transcriber: {key}"
                    )

        # Validate voice configuration if present
        if "voice" in value:
            voice = value.get("voice", {})
            if not isinstance(voice, dict):
                raise serializers.ValidationError("voice must be an object")

            voice_keys = ["provider", "voice", "model"]
            for key in voice_keys:
                if key not in voice:
                    raise serializers.ValidationError(
                        f"Missing required key in voice: {key}"
                    )

        # Validate quality if present
        if "quality" in value:
            quality = value.get("quality", "")
            if not isinstance(quality, str):
                raise serializers.ValidationError("Quality must be a string")

            quality_keys = ["high", "good"]
            if quality not in quality_keys:
                raise serializers.ValidationError(
                    f"Quality must be one of: {', '.join(quality_keys)}"
                )

        # Validate telephony list if present
        if "telephony" in value:
            telephony = value.get("telephony", [])
            if not isinstance(telephony, list):
                raise serializers.ValidationError("telephony must be a list")

        return value

    def create(self, validated_data):
        """
        Phase 2.1: Refactored to use PilotService for business logic.

        This method now delegates to PilotService.create_pilot_with_associations()
        which handles all association creation in a centralized, testable manner.
        """
        from unpod.core_components.services import PilotService

        request = self.context.get("request")
        return PilotService.create_pilot_with_associations(validated_data, request)

    def update(self, pilot, validated_data):
        """
        Phase 2.1: Refactored to use PilotService for business logic.

        This method now delegates to PilotService.update_pilot_with_associations()
        which handles all association updates in a centralized, testable manner.
        """
        from unpod.core_components.services import PilotService

        request = self.context.get("request")
        return PilotService.update_pilot_with_associations(pilot, validated_data, request)


class VespaPilotSerializer(serializers.Serializer):
    handle = serializers.CharField(required=True)
    persona_name = serializers.CharField(required=True)
    about = serializers.CharField(required=True)
    persona = serializers.CharField(required=True)
    tags = serializers.ListField(
        child=serializers.CharField(), required=False, allow_null=True, default=[]
    )
    questions = serializers.ListField(
        child=serializers.CharField(), required=False, allow_null=True, default=[]
    )
    llm_model = serializers.CharField(required=False)

    # Extra Fields
    # knowledge_bases = serializers.ListField(child=serializers.CharField(), required=False, allow_null=True, default=[])

    def validate_handle(self, value):
        # URL decode the handle (converts %C3%A9 to é)
        decoded_value = unquote(value)

        # Slugify to remove special characters and convert to ASCII
        sanitized_value = slugify(decoded_value, allow_unicode=False)

        if not sanitized_value:
            raise serializers.ValidationError(
                "Handle must contain at least some alphanumeric characters"
            )

        # Check if the sanitized handle already exists
        if self.instance:
            exists = (
                Pilot.objects.filter(handle=sanitized_value)
                .exclude(id=self.instance.id)
                .exists()
            )
        else:
            exists = Pilot.objects.filter(handle=sanitized_value).exists()

        if exists:
            raise serializers.ValidationError("Pilot handle is already taken")

        return sanitized_value

    def validate(self, attrs):
        validated_data = super().validate(attrs)
        validated_data["config"] = {}
        rename_fields = {
            "persona_name": "name",
            "about": "description",
            "persona": "ai_persona",
        }
        for old, new in rename_fields.items():
            if old in validated_data:
                validated_data[new] = validated_data.pop(old)
        if "llm_model" in validated_data and validated_data["llm_model"]:
            llm_model = validated_data.pop("llm_model")
            llm_model, created = Model.objects.get_or_create(
                slug=slugify(llm_model),
                model_type=ModelTypes.CHAT.name,
                defaults={"name": llm_model.title().replace("-", " ")},
            )
            validated_data["llm_model_id"] = llm_model.id
        return validated_data

    def create(self, validated_data):
        with transaction.atomic():
            request = self.context.get("request")
            domain_handle = "recalll.co"
            if domain_handle is None:
                raise APIException206(detail={"message": "Org-Handle header not found"})
            org = SpaceOrganization.objects.filter(domain_handle=domain_handle).first()
            validated_data["owner"] = org
            validated_data["created_by"] = request.user.id
            validated_data["state"] = "published"
            tags = validated_data.pop("tags", [])
            user_list = validated_data.pop("user_list", [])
            pilot = Pilot.objects.create(**validated_data)
            PilotLink.objects.create(
                pilot=pilot,
                content_object=request.user,
                link_config={"role_code": "owner"},
            )
            permissions = PilotPermissionSerializer(
                data=user_list, many=True, context={"request": request, "pilot": pilot}
            )
            permissions.is_valid(raise_exception=True)
            permissions.save()
            for tag in tags:
                tag_obj, _ = Tag.objects.get_or_create(
                    name__iexact=tag, defaults={"name": tag}
                )
                pilot.tags.add(tag_obj)
            return pilot


class VoiceProfilesSerializer(serializers.ModelSerializer):
    class Meta:
        model = VoiceProfiles
        fields = "__all__"


class VoiceProfilesRetrieveSerializer(serializers.ModelSerializer):
    transcriber = serializers.SerializerMethodField()
    voice = serializers.SerializerMethodField()
    chat_model = serializers.SerializerMethodField()

    class Meta:
        model = VoiceProfiles
        fields = [
            "agent_profile_id",
            "name",
            "quality",
            "gender",
            "transcriber",
            "voice",
            "voice_temperature",
            "voice_speed",
            "chat_model",
            "temperature",
            # "first_message",
            "greeting_message",
            "description",
            "voice_prompt",
            "estimated_cost",
            "latency",
        ]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        return representation

    def get_transcriber(self, obj):
        stt_languages = obj.stt_language.all()
        return {
            "name": obj.stt_provider.name if obj.stt_provider else None,
            "provider": obj.stt_provider.id if obj.stt_provider else None,
            "model": obj.stt_model.codename if obj.stt_model else None,
            "languages": [{"code": lang.code, "name": lang.name} for lang in stt_languages],
        }

    def get_voice(self, obj):
        languages = obj.tts_language.all()
        return {
            "name": obj.tts_provider.name if obj.tts_provider else None,
            "provider": obj.tts_provider.id if obj.tts_provider else None,
            "voice": obj.tts_voice.code if obj.tts_voice else None,
            "model": obj.tts_model.codename if obj.tts_model else None,
            "languages": [{"code": lang.code, "name": lang.name} for lang in languages],
        }

    def get_chat_model(self, obj):
        return {
            "name": obj.llm_provider.name if obj.llm_provider else None,
            "slug": obj.llm_model.slug if obj.llm_model else None,
            "codename": obj.llm_model.codename if obj.llm_model else None,
            "provider": obj.llm_provider.id if obj.llm_provider else None,
        }


class GlobalSystemConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = GlobalSystemConfig
        fields = "__all__"


class PilotTemplateListSerializer(serializers.ModelSerializer):
    """Serializer for listing templates (lightweight)"""
    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = PilotTemplate
        fields = (
            "id",
            "name",
            "slug",
            "category",
            "description",
            "thumbnail_url",
            "display_order",
            "use_count",
        )

    def get_thumbnail_url(self, obj):
        if obj.thumbnail:
            return obj.thumbnail.url
        return None


class UseCasesSerializer(serializers.ModelSerializer):
    """Serializer for UseCases listing."""
    icon_url = serializers.SerializerMethodField()

    class Meta:
        model = UseCases
        fields = (
            "name",
            "slug",
            "description",
            "icon_url",
            "prompt",
            "skills",
            "required_info",
            "background_gradient",
            "svg_icon",
            "sort_order",
        )

    def get_icon_url(self, obj):
        if obj.icon:
            return obj.icon.url
        return None


class KnowledgebaseEvalsSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=["pilot", "knowledgebase"], default="pilot")
    kn_token = serializers.CharField(required=False, allow_blank=True)
    pilot_handle = serializers.CharField(required=False, allow_blank=True)
    force = serializers.BooleanField(default=False, required=False)

    def validate(self, attrs):
        from unpod.space.utils import checkPostSpaceAccess

        gen_type = attrs.get("type")
        kn_token = attrs.get("kn_token")
        pilot_handle = attrs.get("pilot_handle")
        request = self.context.get("request")

        if gen_type == "pilot":
            if not pilot_handle:
                raise serializers.ValidationError({"pilot_handle": "Pilot handle is required"})
            pilot = Pilot.objects.filter(handle=pilot_handle).first()
            if not pilot:
                raise serializers.ValidationError({"pilot_handle": "Pilot not found"})
            attrs["pilot"] = pilot

        if gen_type == "knowledgebase":
            if not kn_token:
                raise serializers.ValidationError({"kn_token": "Knowledge-base token is required"})
            kn_base = checkPostSpaceAccess(request.user, token=kn_token, check_op=True)
            if not kn_base:
                raise serializers.ValidationError({"kn_token": "Knowledge-base not found"})
            attrs["kn_base"] = kn_base

        return attrs
