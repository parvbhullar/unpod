from unpod.common.enum import ModelBasicStatus, SpaceType
from unpod.common.storage_backends import muxBackend
from unpod.core_components.events import (
    prepare_event_base,
    prepase_event_config,
    process_send_post_email,
)
from unpod.core_components.models import EventsTriggerManager, MediaResource, TelephonyNumber, PilotLink, Plugin
from unpod.core_components.serializers import (
    MediaDataUploadSerializer,
    MediaListSerializer,
    MediaUploadSerializer,
)
from unpod.common.exception import APIException206
from unpod.space.models import Space


def fetch_object_media(
    object_type, object_id, media_relation=None, limit=None, skip=None
):
    query = {"object_type": object_type, "object_id": str(object_id)}
    if media_relation:
        query.update({"media_relation": media_relation})
    # media_values = ['sequence_number', 'public_id', 'name', 'url', 'media_type', 'media_relation', 'size', 'media_id']
    media_data = MediaResource.objects.filter(**query)
    if limit and skip:
        bottom = skip
        top = bottom + limit
        media_count = media_data.count()
        if top >= media_count:
            top = media_count
        media_data = media_data[bottom:top]
    media_data = MediaListSerializer(media_data, many=True).data
    return media_data


def getMediaData(object_type, object_id, media_relation, media_id):
    query = {
        "object_type": object_type,
        "object_id": str(object_id),
        "media_id": media_id,
        "media_relation": media_relation,
    }
    media_values = [
        "sequence_number",
        "public_id",
        "name",
        "media_type",
        "media_relation",
        "size",
        "media_id",
    ]
    media_data = MediaResource.objects.filter(**query).values(*media_values).first()
    if media_data:
        media_data["name"] = media_data["name"].encode().decode("unicode-escape")
    return media_data


def upload_media(
    request, object_type, object_id, media_relation, file=None, media_data=None
):
    if file:
        media_data = {
            "object_type": object_type,
            "object_id": str(object_id),
            "file": file,
            "media_relation": media_relation,
        }
        ser = MediaUploadSerializer(data=media_data, context={"request": request})
        if ser.is_valid():
            instance = ser.upload(ser.validated_data)
            return instance
        return None
    if media_data:
        data = {
            "object_type": object_type,
            "object_id": str(object_id),
            "media_relation": media_relation,
            "media_data": media_data,
        }
        ser = MediaDataUploadSerializer(data=data, context={"request": request})
        if ser.is_valid():
            instance = ser.upload_media(ser.validated_data)
            return instance
        return None


def upload_media_custom(object_type, object_id, media_relation, media_data, user):
    data = {
        "object_type": object_type,
        "object_id": str(object_id),
        "media_relation": media_relation,
        "media_data": media_data,
    }
    ser = MediaDataUploadSerializer(data=data, context={"user": user})
    if ser.is_valid():
        instance = ser.upload_media_custom(ser.validated_data)
        return instance
    return None


def validateMuxMedia(media_data):
    upload_id = media_data["upload_id"]
    upload_res, status = muxBackend.getUploadData(upload_id)
    if status:
        upload_status = upload_res.get("status")
        if upload_status != "asset_created":
            raise APIException206({"message": "Asset Not Upload At Our Provider"})
        media_data["asset_id"] = upload_res.get("asset_id")
        upload_res.pop("url", "")
        media_data["storage_data"] = upload_res
        return media_data, status
    return upload_res, status


def validateMedia(media_id, object_type):
    media_obj = MediaResource.objects.filter(
        media_id=media_id, object_type=object_type
    ).first()
    if not media_obj:
        raise APIException206({"message": "Invalid Media Id"})
    return media_obj


def update_media_status(media_id, object_type, media_status, extra={}):
    query = {}
    if isinstance(media_id, list):
        query = {"media_id__in": media_id}
    else:
        query = {"media_id": media_id}
    MediaResource.objects.filter(object_type=object_type, **query).update(
        media_status=media_status, **extra
    )
    return True


def create_event_trigger(event_name, obj):
    event_data = {"event_name": event_name, **prepare_event_base(event_name)}
    event_data["event_config"] = prepase_event_config(event_name, obj)
    obj = EventsTriggerManager.objects.create(**event_data)
    return obj


def process_trigger_event(event):
    event_func = {"send_post_email": process_send_post_email}
    try:
        status, message = event_func[event.event_name](event)
        return {"success": status, "message": message}
    except Exception as ex:
        return {"success": False, "message": str(ex)}


def process_event_cron():
    events = EventsTriggerManager.objects.filter(status=False, retry__lte=3)[:10]
    for event in events:
        res = process_trigger_event(event)
        if res.get("success", False):
            message = res.get("message")
            EventsTriggerManager.objects.filter(pk=event.pk).update(
                status=True, message=message
            )
        elif res.get("success", False) == "wait":
            continue
        else:
            retry = event.retry + 1
            message = res.get("message")
            EventsTriggerManager.objects.filter(pk=event.pk).update(
                retry=retry, message=message
            )
    return f"Total Cron event processed {len(events)}"


# Phase 2.1: Pilot Business Logic Service Layer
# Extracted from PilotCombinedSerializer to follow service layer pattern

from collections import defaultdict
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
import json


class PilotService:
    """
    Service layer for Pilot creation and update business logic.

    Phase 2.1 Optimization: Extracted from PilotCombinedSerializer to:
    - Separate business logic from data validation
    - Enable reusability across different serializers/views
    - Improve testability and maintainability
    - Centralize complex association logic

    Performance Impact:
    - No query optimization (handled separately)
    - Improved code organization and maintainability
    - Better transaction management
    """

    @staticmethod
    def encode_text_fields(text):
        """
        Encode text using unicode-escape for database storage.

        Args:
            text: String to encode

        Returns:
            Encoded string safe for database storage
        """
        if not text:
            return text
        return text.encode("unicode-escape").decode("utf-8")

    @staticmethod
    def process_pilot_models(pilot, validated_data):
        """
        Process and assign LLM and embedding models to pilot.

        Args:
            pilot: Pilot instance to update
            validated_data: Dict containing chat_model and/or embedding_model

        Raises:
            APIException206: If specified models are not found
        """
        from unpod.core_components.models import Model

        # Handle chat model
        if "chat_model" in validated_data:
            chat_model_data = validated_data.pop("chat_model")
            if isinstance(chat_model_data, str):
                chat_model_data = json.loads(chat_model_data)

            provider = chat_model_data.get("provider")
            codename = chat_model_data.get("codename")
            llm_model = Model.objects.filter(
                codename=codename,
                provider_id=provider,
                status=ModelBasicStatus.active.name
            ).first()

            if llm_model is None:
                raise APIException206(detail={"message": "Chat Model Not Found"})
            pilot.llm_model = llm_model

        # Handle embedding model
        if "embedding_model" in validated_data:
            embedding_data = validated_data.pop("embedding_model")
            if isinstance(embedding_data, str):
                embedding_data = json.loads(embedding_data)

            provider = embedding_data.get("provider")
            codename = embedding_data.get("codename")
            embedding_model = Model.objects.filter(
                codename=codename,
                provider_id=provider,
                status=ModelBasicStatus.active.name
            ).first()

            if embedding_model is None:
                raise APIException206(detail={"message": "Embedding Model Not Found"})
            pilot.embedding_model = embedding_model

    @staticmethod
    def process_pilot_tags(pilot, tags):
        """
        Process tag associations for pilot.

        For create: Adds tags to new pilot
        For update: Clears existing tags and adds new ones

        Args:
            pilot: Pilot instance
            tags: List of tag names (strings)
        """
        from unpod.core_components.models import Tag

        if tags is None:
            return

        # For updates, clear existing tags
        if pilot.pk:
            pilot.tags.clear()

        # Add all tags (get_or_create for each)
        for tag_name in tags:
            tag, _ = Tag.objects.get_or_create(name=tag_name)
            pilot.tags.add(tag)

    @staticmethod
    def process_pilot_telephony(pilot, telephony_config, is_update=False):
        """
        Process telephony number associations for pilot.

        Args:
            pilot: Pilot instance
            telephony_config: Dict with 'telephony' key containing number configs
            is_update: Boolean indicating if this is an update operation
        """

        telephony = telephony_config.get("telephony", None)
        if not telephony or len(telephony) == 0:
            return

        # Extract number IDs from config
        numbers_ids = [item["id"] for item in telephony if item.get("id")]

        # Validate that numbers exist
        valid_ids = TelephonyNumber.objects.filter(id__in=numbers_ids).values_list(
            "id", flat=True
        )

        if valid_ids:
            # For updates, clear existing associations
            if is_update:
                pilot.numbers.clear()

            # Associate numbers with pilot
            pilot.numbers.add(*valid_ids)

    @staticmethod
    def process_pilot_plugins(pilot, plugins, is_update=False):
        """
        Process plugin associations via PilotLink.

        Args:
            pilot: Pilot instance
            plugins: List of plugin slugs
            is_update: Boolean indicating if this is an update operation

        Raises:
            APIException206: If any plugins are not found
        """

        if plugins is None:
            return

        # Validate all plugins exist
        plugin_count = Plugin.objects.filter(slug__in=plugins).count()
        if plugin_count != len(plugins):
            raise APIException206(detail={"message": "Plugins Not Found"})

        plugin_objs = Plugin.objects.filter(slug__in=plugins)
        content_type = ContentType.objects.get_for_model(Plugin)

        # For updates, delete existing plugin links
        if is_update:
            PilotLink.objects.filter(
                pilot=pilot,
                content_type=content_type,
            ).delete()

        # Bulk create new plugin links
        PilotLink.objects.bulk_create(
            [PilotLink(pilot=pilot, content_object=plugin) for plugin in plugin_objs]
        )

    @staticmethod
    def process_pilot_knowledge_bases(pilot, knowledge_bases, is_update=False):
        """
        Process knowledge base associations via PilotLink.

        Args:
            pilot: Pilot instance
            knowledge_bases: List of space slugs (knowledge base type)
            is_update: Boolean indicating if this is an update operation

        Raises:
            APIException206: If any knowledge bases are not found
        """

        if knowledge_bases is None:
            return

        # Validate all knowledge bases exist
        kb_count = Space.objects.filter(
            slug__in=knowledge_bases, space_type=SpaceType.knowledge_base.name
        ).count()

        if kb_count != len(knowledge_bases):
            raise APIException206(detail={"message": "Knowledge Bases Not Found"})

        kbs = Space.objects.filter(
            slug__in=knowledge_bases, space_type=SpaceType.knowledge_base.name
        )

        content_type = ContentType.objects.get_for_model(Space)

        # For updates, delete existing KB links
        if is_update:
            PilotLink.objects.filter(
                pilot=pilot,
                content_type=content_type,
                spaces__space_type=SpaceType.knowledge_base.name,
            ).delete()

        # Bulk create new KB links
        PilotLink.objects.bulk_create(
            [PilotLink(pilot=pilot, content_object=kb) for kb in kbs]
        )

    @staticmethod
    def process_pilot_components(pilot, components, request):
        """
        Process component form values for pilot.

        Components are dynamic form configurations stored as DynamicFormValues.
        Input format: {"component_slug__field_name": value, ...}

        Args:
            pilot: Pilot instance
            components: Dict with format {slug__field: value}
            request: Request object for user context
        """
        from unpod.dynamic_forms.models import DynamicForm, DynamicFormValues

        if not components:
            return

        # Group component data by slug
        components_data = defaultdict(dict)
        for key, value in components.items():
            slug, field = key.split("__", 1)
            if field == "options":
                value = value or {}
            components_data[slug][field] = value

        # Create or update form values for each component
        for slug, values in components_data.items():
            form = DynamicForm.objects.filter(
                slug=slug,
                type="component",
                parent_type="agent",
                status="active",
            ).first()

            if not form:
                continue

            form_values, created = DynamicFormValues.objects.get_or_create(
                form=form,
                parent_type="agent",
                parent_id=pilot.handle,
                defaults={
                    "name": form.name,
                    "values": values,
                    "created_by": request.user,
                },
            )

            if not created:
                form_values.values = values
                form_values.save()

    @staticmethod
    def process_pilot_permissions(pilot, user_list, request):
        """
        Process user permissions for pilot via PilotPermissionSerializer.

        Args:
            pilot: Pilot instance
            user_list: Dict containing user permission data
            request: Request object for context
        """
        from unpod.core_components.serializers import PilotPermissionSerializer
        from django.contrib.auth import get_user_model

        User = get_user_model()

        if not user_list:
            return

        # Delete existing user links except for owner
        pilot.link_qs.filter(
            content_type=ContentType.objects.get_for_model(User)
        ).exclude(link_config__role_code="owner").delete()

        # Create new permissions using serializer
        permissions = PilotPermissionSerializer(
            data=user_list,
            many=True,
            context={"request": request, "pilot": pilot},
        )
        permissions.is_valid(raise_exception=True)
        permissions.save()

    @staticmethod
    def process_pilot_eval_kbs(pilot, eval_kn_bases, is_update=False):
        """
        Process eval_kn_bases associations for pilot.

        For create: Adds eval_kn_bases to new pilot
        For update: Clears existing eval_kn_bases and adds new ones

        Args:
            pilot: Pilot instance
            eval_kn_bases: List of tag names (strings)
        """
        from unpod.core_components.models import Tag

        if eval_kn_bases is None:
            return

        # Validate all knowledge bases exist
        kb_count = Space.objects.filter(
            slug__in=eval_kn_bases, space_type=SpaceType.knowledge_base.name
        ).count()

        if kb_count != len(eval_kn_bases):
            raise APIException206(detail={"message": "Knowledge Bases Not Found"})

        valid_ids = (Space.objects.filter(slug__in=eval_kn_bases, space_type=SpaceType.knowledge_base.name)
        .values_list(
            "id", flat=True)
        )

        if valid_ids:
            # For updates, clear existing associations
            if is_update:
                pilot.eval_kn_bases.clear()

            # Associate numbers with pilot
            pilot.eval_kn_bases.add(*valid_ids)

    @staticmethod
    @transaction.atomic
    def create_pilot_with_associations(validated_data, request):
        """
        Main orchestration method for creating a Pilot with all associations.

        Handles:
        - Model lookups (LLM, embedding)
        - Pilot instance creation
        - Tag associations
        - Telephony number associations
        - Plugin associations (via PilotLink)
        - Knowledge base associations (via PilotLink)
        - User permissions
        - Component form values

        Args:
            validated_data: Validated data from serializer
            request: Request object for user context

        Returns:
            Created Pilot instance with all associations
        """
        from unpod.core_components.models import Pilot, Model
        from unpod.space.models import Space, SpaceOrganization
        from unpod.core_components.models import PilotTemplate
        from unpod.common.enum import ModelTypes

        # Extract association data from validated_data
        tags = validated_data.pop("tags", [])
        user_list = validated_data.pop("user_list", {})
        plugins = validated_data.pop("plugins", [])
        knowledge_bases = validated_data.pop("knowledge_bases", [])
        space_slug = validated_data.pop("space_slug", None)
        components = validated_data.pop("components", None)
        template_slug = validated_data.pop("template", "")
        telephony_config = validated_data.get("telephony_config", {})
        chat_model = validated_data.get("chat_model", None)
        org_handle = request.headers.get("Org-Handle", None)
        eval_kn_bases = validated_data.pop("eval_kn_bases", [])

        # Handle model associations
        if chat_model:
            chat_model_data = (
                json.loads(chat_model) if isinstance(chat_model, str) else chat_model
            )
            llm_model = Model.objects.filter(
                codename=chat_model_data.get("codename"),
                model_type=ModelTypes.CHAT.name,
            ).first()
            if llm_model is None:
                raise APIException206(detail={"message": "Chat Model Not Found"})
            validated_data["llm_model"] = llm_model

        # Get the organization
        if org_handle:
            organization = SpaceOrganization.objects.filter(
                domain_handle=org_handle
            ).first()
            validated_data["owner"] = organization

        # Handle template
        if template_slug:
            template = PilotTemplate.objects.filter(slug=template_slug).first()
            if template:
                validated_data["template"] = template

        # Handle space
        if space_slug:
            space = Space.objects.filter(slug=space_slug).first()
            if space:
                validated_data["space"] = space

        # Set metadata fields
        validated_data["created_by"] = request.user.id

        # Create Pilot instance
        pilot = Pilot.objects.create(**validated_data)

        # Process all associations
        PilotService.process_pilot_tags(pilot, tags)
        PilotService.process_pilot_telephony(pilot, telephony_config, is_update=False)
        PilotService.process_pilot_plugins(pilot, plugins, is_update=False)
        PilotService.process_pilot_knowledge_bases(
            pilot, knowledge_bases, is_update=False
        )
        PilotService.process_pilot_permissions(pilot, user_list, request)
        PilotService.process_pilot_components(pilot, components, request)
        PilotService.process_pilot_eval_kbs(pilot, eval_kn_bases)

        # Set default component values if none provided
        if not components:
            from unpod.dynamic_forms.models import DynamicForm, DynamicFormValues

            forms = DynamicForm.objects.filter(
                parent_type="agent", type="component", status="active"
            )
            for form in forms:
                DynamicFormValues.objects.create(
                    form=form,
                    parent_type="agent",
                    parent_id=pilot.handle,
                    name=form.name,
                    created_by=request.user,
                )

        return pilot

    @staticmethod
    @transaction.atomic
    def update_pilot_with_associations(pilot, validated_data, request):
        """
        Main orchestration method for updating a Pilot with all associations.

        Handles:
        - Model updates (LLM, embedding)
        - Field updates
        - Tag associations (clear + add)
        - Telephony number associations (clear + add)
        - Plugin associations (delete + bulk_create)
        - Knowledge base associations (delete + bulk_create)
        - User permissions (delete + recreate)
        - Component form values (get_or_create + update)

        Args:
            pilot: Existing Pilot instance to update
            validated_data: Validated data from serializer
            request: Request object for user context

        Returns:
            Updated Pilot instance with all associations
        """
        from unpod.space.models import Space
        from unpod.core_components.models import PilotTemplate
        from django.contrib.auth import get_user_model

        User = get_user_model()

        # Extract association data from validated_data
        tags = validated_data.pop("tags", None)
        user_list = validated_data.pop("user_list", {})
        plugins = validated_data.pop("plugins", None)
        knowledge_bases = validated_data.pop("knowledge_bases", None)
        space_slug = validated_data.pop("space_slug", None)
        components = validated_data.pop("components", None)
        template_slug = validated_data.pop("template", "")
        eval_kn_bases = validated_data.pop("eval_kn_bases", None)
        telephony_config = validated_data.get("telephony_config", {})

        # Handle space update
        if space_slug:
            space = Space.objects.filter(slug=space_slug).first()
            if space:
                pilot.space = space

        # Handle template update
        if template_slug:
            template = PilotTemplate.objects.filter(slug=template_slug).first()
            if template:
                validated_data["template"] = template

        # Set metadata fields
        validated_data["updated_by"] = request.user.id

        # Process model updates
        PilotService.process_pilot_models(pilot, validated_data)

        # Update all other fields
        for attr, value in validated_data.items():
            setattr(pilot, attr, value)
        pilot.save()

        # Process all associations (these handle clear/delete internally)
        PilotService.process_pilot_tags(pilot, tags)
        PilotService.process_pilot_telephony(pilot, telephony_config, is_update=True)
        PilotService.process_pilot_knowledge_bases(
            pilot, knowledge_bases, is_update=True
        )
        PilotService.process_pilot_plugins(pilot, plugins, is_update=True)

        # Clean up public pilot user links
        if pilot.privacy_type == "public":
            pilot.link_qs.filter(
                content_type=ContentType.objects.get_for_model(User)
            ).exclude(link_config__role_code="owner").delete()

        # Process user permissions and components
        PilotService.process_pilot_permissions(pilot, user_list, request)
        PilotService.process_pilot_components(pilot, components, request)
        PilotService.process_pilot_eval_kbs(pilot, eval_kn_bases, is_update=True)

        return pilot
