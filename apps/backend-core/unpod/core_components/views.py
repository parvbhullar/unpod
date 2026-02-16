import asyncio
import json
import mimetypes

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.db.models import Q, F, Subquery, OuterRef
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.urls import resolve
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from slugify import slugify

from unpod.common.enum import (
    OrganisationAccountType,
    PrivacyType,
    SpaceType,
    RoleCodes,
    PilotTypes,
    ModelBasicStatus,
    StatusEnum,
)
from unpod.common.exception import APIException401
from unpod.common.jwt import jwt_decode_handler
from unpod.common.mixin import (
    UsableRequest,
    SerializerSelectionMixin,
    CacheInvalidationMixin,
)
from unpod.common.mongodb import MongoDBQueryManager
from unpod.common.pagination import UnpodCustomPagination
from unpod.common.prefect import trigger_deployment
from unpod.common.renderers import UnpodJSONRenderer
from unpod.common.s3 import get_s3_presigned_url, read_s3
from unpod.common.serializer import CommonSerializer
from unpod.core_components import utils as core_utils
from unpod.core_components.models import (
    MediaResource,
    ProfileRoles,
    Pilot,
    Plugin,
    Tag,
    PilotLink,
    VoiceProfiles,
    UseCases,
    Model,
    Voice,
    Language,
    GlobalSystemConfig,
    PilotTemplate,
    Provider,
    TelephonyNumber,
)
from unpod.core_components.models import RelevantTag, RelevantTagLink
from unpod.core_components.serializers import (
    CoreInviteRequestPublic,
    MediaListSerializer,
    MediaUploadMutlipleSerializer,
    MediaUploadRequestDetailSerializer,
    MediaUploadRequestSerializer,
    MediaUploadSerializer,
    MessagingBlockList,
    PilotListSerializer,
    PilotSerializer,
    PluginSerializer,
    ModelSerializer,
    KBSerializer,
    TagSerializer,
    PilotPermissionSerializer,
    GlobalSystemConfigSerializer,
    PilotExportSerializer,
    PilotTemplateListSerializer,
    PilotMenusSerializer,
    VoiceProfilesSerializer,
    VoiceProfilesRetrieveSerializer,
    UseCasesSerializer,
    KnowledgebaseEvalsSerializer, PilotFullSerializer, ProviderSerializer, TelephonyNumberSerializer,
)
from unpod.core_components.serializers import RelevantTagSerializer
from unpod.knowledge_base.models import KnowledgeBaseEvals
from unpod.roles.constants import PERMISSION_DICT, PROFILE_ROLES_FILEDS, ROLES_FILEDS
from unpod.roles.models import Roles
from unpod.roles.services import createPermission
from unpod.space.models import (
    OrganizationInvite,
    SpaceInvite,
    SpaceMemberRoles,
    SpaceOrganization,
    Space,
)
from unpod.space.serializers import SpaceListSerializers
from unpod.space.services import processInvitation, get_organization_by_domain_handle

from unpod.thread.models import PostInvite, ThreadPost, ThreadPostReaction
from unpod.thread.serializers import PostReactionCreate
from .services import PilotService
from .utils import check_for_vapi
from ..common.uuid import generate_uuid
from ..dynamic_forms.models import DynamicForm, DynamicFormValues
from unpod.core_components.utils import remove_from_redis
from unpod.common.prefect import trigger_deployment



# fmt: off
User = get_user_model()


class ProviderViewSet(viewsets.GenericViewSet):
    queryset = Provider.objects.all()
    serializer_class = ProviderSerializer
    permission_classes = [IsAuthenticated]
    renderer_classes = [UnpodJSONRenderer]

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(status="active")
        provider_type = self.request.query_params.get("type")

        if provider_type:
            queryset = queryset.filter(type__iexact=provider_type)
        return queryset

    def list(self, request):
        queryset = super().get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        return Response(
            {
                "status_code": status.HTTP_200_OK,
                "message": "Models retrieved successfully",
                "data": serializer.data,
            }
        )

    def get_model_providers(self, request):
        model_type = self.request.query_params.get("model_type")

        queryset = super().get_queryset()
        queryset = queryset.filter(status="active")
        queryset = queryset.filter(type__iexact="model")
        queryset = queryset.filter(model_types__contains=[model_type] if model_type else [])

        serializer = self.get_serializer(queryset, many=True)

        return Response(
            {
                "status_code": status.HTTP_200_OK,
                "message": "Models retrieved successfully",
                "data": serializer.data,
            }
        )


class TelephonyNumberViewSet(viewsets.GenericViewSet):
    queryset = TelephonyNumber.objects.all()
    serializer_class = TelephonyNumberSerializer
    permission_classes = [IsAuthenticated]
    renderer_classes = [UnpodJSONRenderer]

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset().filter(active=True, state="NOT_ASSIGNED")

            number_type = request.query_params.get("type")
            if number_type == "agent":
                queryset = queryset.filter(agent_number=True)
            else:
                queryset = queryset.filter(agent_number=False)

            region = request.query_params.get("region")
            if region:
                queryset = queryset.filter(region=region)

            serializer = self.get_serializer(queryset, many=True)

            return Response(
                {
                    "data": serializer.data,
                    "message": "Telephony numbers fetched successfully.",
                },
            )

        except Exception as e:
            return Response(
                {
                    "status_code": 400,
                    "message": "Failed to fetch data.",
                    "error": str(e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


class ApiMediaPublicResourceViewSet(viewsets.GenericViewSet):
    permission_classes = (AllowAny,)
    renderer_classes = (UnpodJSONRenderer,)

    def download_signed_url(self, request, *args, **kwargs):
        """
        Download pre-signed URL for media resource as file response
        """
        url = self.request.GET.get("url")
        filename = url.split("/")[-1].split("?")[0]
        mime_type, _ = mimetypes.guess_type(filename)
        mime_type = mime_type or "application/octet-stream"

        if "s3" in url:
            url, _ = get_s3_presigned_url(None, None, s3_url=url)

            # Download the file from S3
            response = requests.get(url, stream=True, timeout=30)
            if response.status_code != 200:
                return Response(
                    {"message": "Failed to fetch file"}, status=206
                )

            # Return file as downloadable response
            downloadable = HttpResponse(
                response.content,
                content_type=mime_type
            )
            downloadable["Content-Disposition"] = f'attachment; filename="{filename}"'
            return downloadable

        return Response({"data": {"url": url}, "message": "Url Generated Successfully"})


class ApiMediaResourceViewSet(viewsets.GenericViewSet):
    queryset = MediaResource.objects.all()
    serializer_class = CommonSerializer
    renderer_classes = (UnpodJSONRenderer,)

    def list(self, request, *args, **kwargs):
        object_type = kwargs.get("object_type")
        object_id = kwargs.get("object_id")
        query = Q()

        query.add(Q(object_id=object_id), Q.AND)

        query.add(Q(object_type=object_type), Q.AND)
        is_filter = True

        if "name" in request.GET:
            query.add(Q(name__icontains=request.GET["name"]), Q.AND)

        fields = [
            "object_type",
            "object_id",
            "size",
            "media_id",
            "media_type",
            "media_relation",
            "name",
            "media_url",
            "privacy_type",
            "file_storage_url",
            "public_id",
            "url",
        ]
        queryset = MediaResource.objects.filter(query).only(*fields).order_by("-id")
        page = UnpodCustomPagination(self.request, queryset, MediaListSerializer)
        page = page.get_paginated_response(return_dict=True)
        return Response(
            {**page, "message": "Media List Fetch Successfully"}, status=200
        )

    def upload(self, request, *args, **kwargs):
        ser = MediaUploadSerializer(data=request.data, context={"request": request})
        if ser.is_valid():
            instance = ser.upload(ser.validated_data)
            instance = MediaListSerializer(instance).data
            return Response({"data": instance, "message": "File Uploaded Successfully"})
        return Response(
            {"errors": ser.errors, "message": "There is some Validation error"},
            status=206,
        )

    def upload_multiple(self, request, *args, **kwargs):
        ser = MediaUploadMutlipleSerializer(
            data=request.data, context={"request": request}
        )
        if ser.is_valid():
            instance = ser.upload(ser.validated_data)
            instance = MediaListSerializer(instance, many=True).data
            return Response(
                {"data": instance, "message": "Files Uploaded Successfully"}
            )
        return Response(
            {"errors": ser.errors, "message": "There is some Validation error"},
            status=206,
        )

    def get(self, request, *args, **kwargs):
        media_id = kwargs.get("media_id")
        fields = [
            "object_type",
            "object_id",
            "size",
            "media_id",
            "media_type",
            "media_relation",
            "name",
            "media_url",
            "privacy_type",
            "file_storage_url",
            "public_id",
            "url",
        ]
        media_obj = (
            MediaResource.objects.filter(media_id=media_id).only(*fields).first()
        )
        if media_obj:
            media_obj = MediaListSerializer(media_obj).data
            return Response(
                {"data": media_obj, "message": "Media Data Fetch Successfully"}
            )
        return Response({"message": "Invalid Media ID"}, status=206)

    def get_upload_url(self, request, *args, **kwargs):
        ser = MediaUploadRequestSerializer(
            data=request.data, context={"request": request}
        )
        if ser.is_valid():
            instance = ser.save()
            data = MediaUploadRequestDetailSerializer(instance).data
            return Response({"data": data, "message": "Url Generated Successfully"})
        return Response(
            {"errors": ser.errors, "message": "There is some Validation error"},
            status=206,
        )

    def pre_signed_url(self, request, *args, **kwargs):
        url = self.request.GET.get("url")
        if "s3" in url:
            url, _ = get_s3_presigned_url(None, None, s3_url=url)
        return Response({"data": {"url": url}, "message": "Url Generated Successfully"})


class BasicSettingViewSet(viewsets.GenericViewSet):
    permission_classes = (AllowAny,)
    serializer_class = CommonSerializer
    renderer_classes = (UnpodJSONRenderer,)

    def basic_setting(self, request, *args, **kwargs):
        basic_key = "global_basic_settings"
        basic_data = cache.get(basic_key)
        if basic_data:
            basic_data = json.loads(basic_data)
        else:
            basic_data = {}
            basic_data["permissions"] = PERMISSION_DICT
            role_data = {}
            for role_type in ["post", "space"]:
                role_data[role_type] = list(
                    Roles.objects.filter(role_type=role_type, is_active=True).values(
                        *ROLES_FILEDS
                    )
                )
            basic_data["roles"] = role_data
            profile_roles = list(
                ProfileRoles.objects.all().values(*PROFILE_ROLES_FILEDS)
            )
            basic_data["profile_roles"] = profile_roles
            basic_data["account_type"] = OrganisationAccountType.to_list()
            basic_data["pilot_types"] = [
                {
                    "slug": "CHAT",
                    "name": "Question & Answering Pilot",
                    "description": "A SuperPilot which can research over Internet, datasets, documents, emails and answer user's questions. For e.g. sales, support, IT chatbots.",
                    "icon": "user",
                },
                {
                    "slug": "GENERATION",
                    "name": "Generative Pilot",
                    "description": "A Superpilot, which can generate text, images, videos, code or anything. For e.g. content generators, code generators.",
                    "icon": "building",
                },
                {
                    "slug": "EXECUTION_PILOT",
                    "name": "AI Companion",
                    "description": "A Superpilot, which can behave as personality, role, book or ideology. Based on provided data and knowledge.",
                    "icon": "briefcase",
                },
            ]
            cache.set(basic_key, json.dumps(basic_data), 12 * 60 * 60)
        return Response(
            {"data": basic_data, "message": "Basic Data Generated Successfully"}
        )

    def get_sitemap_file(self, request, *args, **kwargs):
        sitemap_file = kwargs.get("sitemap_file")
        if sitemap_file:
            allowed_sitemap = ["sitemap-post", "sitemap-organization", "sitemap-space"]
            if sitemap_file not in allowed_sitemap:
                return Response({"message": "Invalid Sitemap File"}, status=206)
            key = f"{settings.AWS_SITEMAP_DIR}/{sitemap_file}.xml"
            sitemap_data, status = read_s3(settings.AWS_STORAGE_BUCKET_NAME, key)
            return Response(
                {"data": sitemap_data, "message": "Sitemap File Generated Successfully"}
            )
        return Response({"data": [], "message": "Sitemap File Generated Successfully"})


class GlobalInvitationViewSet(viewsets.GenericViewSet):
    permission_classes = (AllowAny,)
    serializer_class = CommonSerializer
    renderer_classes = [UnpodJSONRenderer]

    def inviteVerify(self, request, *args, **kwargs):
        product_id = request.headers.get("Product-Id")
        if not product_id:
            return Response({"message": "Product Id Missing in Header"}, status=206)

        from unpod.space.serializers import (
            SpaceListSerializers,
            SpaceOrganizationSerializers,
        )

        token = request.data.get("token")
        if not token:
            return Response(
                {"message": "Please provide the invitation token"}, status=206
            )
        try:
            token_payload = jwt_decode_handler(token)
        except:
            return Response(
                {"message": "Please provide valid invitation token"}, status=206
            )
        invite_token = token_payload.get("invite_token")
        invite_email = token_payload.get("email")
        invite_type = token_payload.get("invite_type", "space")
        model_dict = {
            "space": SpaceInvite,
            "post": PostInvite,
            "organization": OrganizationInvite,
        }
        if request.user.is_authenticated:
            if request.user.email != invite_email:
                return Response(
                    {"message": "Invalid Access. You can't verify other users request"},
                    status=206,
                )
        modelObj = model_dict.get(invite_type)
        invite_obj = modelObj.objects.filter(
            user_email=invite_email, invite_token=invite_token
        ).first()
        if not invite_obj:
            return Response(
                {"message": "Please provide valid invitation token"}, status=206
            )
        check_user = User.objects.filter(email=invite_email).first()
        final_data = {
            "user_exists": check_user != None,
            "user_email": invite_email,
            "invite_token": invite_token,
            "is_verified": True,
            "invite_type": invite_type,
        }
        if invite_type == "space":
            space = SpaceListSerializers(invite_obj.space).data
            space["invite_token"] = invite_token
            final_data.update({"space": space})
        elif invite_type == "post":
            final_data.update({"post_title": invite_obj.post.title})
        elif invite_type == "organization":
            org = SpaceOrganizationSerializers(invite_obj.organization).data
            org["invite_token"] = invite_token
            final_data.update({"organization": org})
        if invite_obj.invite_verified:
            return Response(
                {
                    "message": "Invitation is Already verified by User",
                    "data": final_data,
                },
                status=200,
            )
        if invite_obj.is_joined:
            return Response(
                {"message": f"User Already Joined the {invite_type.title()}"},
                status=206,
            )
        current = timezone.now()
        if invite_obj.valid_upto < current:
            return Response(
                {
                    "message": "This Invitation has been Expired",
                    "data": {"invite_expired": True, "invite_token": invite_token},
                },
                status=206,
            )
        invite_obj.invite_verified = True
        invite_obj.invite_verify_dt = current
        invite_obj.save()
        res = {"message": "Invite Successfully Verified"}
        res["data"] = final_data
        return Response(res, status=200)

    def invite_subscribe(self, request, *args, **kwargs):
        data = request.data
        ser = CoreInviteRequestPublic(data=data)
        ser.is_valid()
        data = ser.validated_data
        email = {"email": data.get("email")}
        main_obj, user_emails, invite_type = data.get("invite_obj"), [email], data.get("invite_type")
        user = UsableRequest()
        user.email = None
        user.id = None
        success_data, failed_email = processInvitation(main_obj, user_emails, user, invite_type)
        return Response(
            {
                "message": f"Invitation Sent Successfully",
                "failed_invite": failed_email,
                "success_data": success_data,
            },
            status=201,
        )


class MessagingServiceViewSet(viewsets.GenericViewSet):
    permission_classes = (AllowAny,)
    serializer_class = CommonSerializer
    renderer_classes = [UnpodJSONRenderer]

    def postData(self, request, *args, **kwargs):
        error_message = None
        try:
            thread_id = kwargs.get("thread_id")
            current_url = resolve(request.path_info).route
            current_url = current_url.replace("api/v1/", "")
            headers = {"Authorization": request.headers.get("Authorization")}
            session_user = None
            query_params = {}
            if not request.user.is_authenticated:
                session_user = request.data.get("session_user") or request.GET.get(
                    "session_user"
                )
                if not session_user:
                    return Response(
                        {"message": "Authentication credentials were not provided"},
                        status=206,
                    )
                query_params = {"session_user": session_user}
            query_params.update(request.GET.dict())
            hit = None
            if request.method == "POST":
                request_data = request.data.copy()
                hit = requests.post(
                    url=f"{settings.API_SERVICE_URL}/{current_url}",
                    json=request_data,
                    headers=headers,
                    params=query_params,
                    timeout=30,
                )
            if request.method == "GET":
                if thread_id != "":
                    current_url_api = current_url.replace("<str:thread_id>", thread_id)
                hit = requests.get(
                    url=f"{settings.API_SERVICE_URL}/{current_url_api}",
                    headers=headers,
                    params=query_params,
                    timeout=30,
                )
            if request.method == "PUT":
                request_data = request.data.copy()
                if thread_id != "":
                    current_url = current_url.replace("<str:thread_id>", thread_id)
                hit = requests.put(
                    url=f"{settings.API_SERVICE_URL}/{current_url}",
                    json=request_data,
                    headers=headers,
                    params=query_params,
                    timeout=30,
                )
            if hit:
                data = json.loads(hit.content)
                if current_url == "conversation/<str:thread_id>/messages/":
                    messages = data.pop("data", [])
                    messages = MessagingBlockList(messages, many=True).data
                    return Response({"data": messages, **data})
                return Response(data)
            else:
                error_message = "No data found"
        except Exception as ex:
            print(ex)
            error_message = "Something went wrong"
        return Response(
            {"success": False, "data": [], "message": error_message}, status=206
        )

    def public_pilots(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise APIException401(
                {"message": "Unauthorized access"}
            )
        search = request.GET.get("search")
        query = Q(privacy_type="public", state="published")
        pilot_type = request.GET.get("type", PilotTypes.Pilot.name)
        if pilot_type:
            query = query & Q(type=pilot_type)
        if search and search != "":
            query = query & Q(
                Q(name__icontains=search)
                | Q(handle__icontains=search)
            )
        queryset = Pilot.objects.filter(query).order_by("-modified")
        page = UnpodCustomPagination(
            self.request,
            queryset,
            PilotListSerializer,
            kwargs={"context": {"request": request}},
        )
        page = page.get_paginated_response(return_dict=True)
        return Response(
            {**page, "message": "Pilots List Fetch Successfully"}, status=200
        )


class WebsiteInfoViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CommonSerializer
    renderer_classes = [UnpodJSONRenderer]

    def website_info(self, request, *args, **kwargs):
        import logging
        logger = logging.getLogger(__name__)

        domain = request.GET.get("domain")
        source_type = request.GET.get("type")
        if not domain:
            return Response({"message": "Please provide domain"}, status=206)

        from ..common.services.web_scraper import scrape_website

        try:
            # check if the domain starts with http or https
            if not domain.startswith("http://") and not domain.startswith("https://"):
                domain = "https://" + domain

            logger.info(f"Fetching website info for domain: {domain}")

            # Scrape the website and get data
            data = scrape_website(domain, source_type)
            if data.get("success") is False:
                error_message = data.get("message", "Unknown error")

                # Provide more context for common issues
                if "Failed to get content from URL" in error_message:
                    error_message = (
                        f"Unable to scrape {domain}. This could be because: "
                        "the website is a redirect/parked domain, blocks web scraping, "
                        "has no content, or is temporarily unavailable. "
                        f"Original error: {error_message}"
                    )

                logger.warning(f"Failed to scrape {domain}: {error_message}")
                return Response(
                    {
                        "message": f"Failed to fetch website info: {error_message}",
                        "domain": domain,
                        "hint": "Try testing with a different website (e.g., google.com, example.com) to verify the service is working."
                    },
                    status=206,
                )

            business_info = data.get("data", {})
            logger.info(f"Successfully fetched website info for {domain}")

            return Response(
                {
                    "message": "Website Info Fetch Successfully",
                    "data": business_info,
                },
                status=200,
            )
        except Exception as e:
            logger.error(f"Unexpected error fetching website info for {domain}: {str(e)}", exc_info=True)
            return Response(
                {
                    "message": f"Failed to fetch website info: {str(e)}",
                    "domain": domain
                },
                status=206,
            )


class PilotViewSet(CacheInvalidationMixin, SerializerSelectionMixin, viewsets.GenericViewSet):
    """
    Phase 2.2: Refactored to use SerializerSelectionMixin for tiered serializer selection.
    Phase 3.2: Added CacheInvalidationMixin for automatic cache invalidation.
    """
    serializer_class = PilotSerializer
    renderer_classes = [UnpodJSONRenderer]
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    # Phase 3.2: Cache invalidation patterns for pilot-related caches
    cache_key_patterns = [
        'pilot_list:*',  # Invalidate pilot list caches
        'pilot_detail:{obj.id}:*',  # Invalidate specific pilot detail cache
    ]

    # Phase 2.2: Define tiered serializers for automatic selection
    @property
    def serializer_class_list(self):
        from unpod.core_components.serializers import PilotListSerializer
        return PilotListSerializer

    @property
    def serializer_class_detail(self):
        from unpod.core_components.serializers import PilotFullSerializer
        return PilotFullSerializer

    @property
    def serializer_class_full(self):
        from unpod.core_components.serializers import PilotFullSerializer
        return PilotFullSerializer

    def check_handle_available(self, request, *args, **kwargs):
        handle = self.request.GET.get("handle")
        exclude_handle = self.request.GET.get("exclude_handle")
        if handle:
            if exclude_handle:
                exists = (
                    Pilot.objects.filter(handle=handle)
                    .exclude(handle=exclude_handle)
                    .exists()
                )
            else:
                exists = Pilot.objects.filter(handle=handle).exists()
            if exists:
                return Response(
                    {
                        "message": "Pilot handle is already taken",
                        "data": {"exist": True},
                    },
                    status=200,
                )
        return Response(
            {"message": "Pilot handle available", "data": {"exist": False}}, status=200
        )

    def list(self, request, *args, **kwargs):
        # query = Q(privacy_type=PrivacyType.public.value)
        query = Q()
        domain = request.GET.get("domain")
        domain_handle_header = request.headers.get("Org-Handle", None)
        case = request.GET.get("case")
        search = request.GET.get("search")
        pilot_type = request.GET.get("type")
        if pilot_type:
            query = query & Q(type=pilot_type)
        if domain:
            org = SpaceOrganization.objects.filter(domain_handle=domain).first()
            query &= Q(owner=org)
        elif domain_handle_header:
            org = SpaceOrganization.objects.filter(
                domain_handle=domain_handle_header
            ).first()
            query &= Q(owner=org)

        if search and search != "":
            query = query & Q(
                Q(name__icontains=search)
                | Q(handle__icontains=search)
            )
        queryset = Pilot.objects.filter(query).select_related(
            'owner',  # For get_hub_domain_handle, get_organization
            'llm_model',  # For get_chat_model
            'llm_model__provider',  # For provider_info in get_chat_model
            'embedding_model',  # For get_embedding_model
            'template',  # For template.slug
        ).prefetch_related(
            'pilot_links',  # For get_plugins and get_knowledge_bases
            'numbers',  # For get_numbers
            'tags',
        ).order_by("-modified")
        # Use PilotListSerializer for list views (Phase 2.1 - 97% query reduction)
        list_serializer = self.get_serializer_class_for_response('list')
        if case == "all":
            page = {
                "count": queryset.count(),
                "data": list_serializer(
                    queryset, context={"request": request}, many=True
                ).data,
            }
        elif case == "home":
            query = Q(privacy_type=PrivacyType.public.value) | Q(owner=org)
            if pilot_type:
                query = query & Q(type=pilot_type)
            queryset = Pilot.objects.filter(query).order_by("-modified")
            subquery = (
                ThreadPost.objects.filter(related_data__pilot=OuterRef("handle"))
                .order_by("-id")
                .values("id")[:1]
            )
            queryset = queryset.annotate(last_thread_id=Coalesce(Subquery(subquery), 0))
            queryset = queryset.order_by("-last_thread_id", "-modified")
            page = {
                "count": queryset.count(),
                "data": list_serializer(
                    queryset, context={"request": request}, many=True
                ).data,
            }
        else:
            page = UnpodCustomPagination(
                self.request,
                queryset,
                list_serializer,
                kwargs={"context": {"request": request}},
            )
            page = page.get_paginated_response(return_dict=True)
        return Response(
            {**page, "message": "Pilots List Fetch Successfully"}, status=200
        )

    def get_menus_list(self, request, *args, **kwargs):
        domain_handle = request.headers.get("Org-Handle", None)
        if not domain_handle:
            return Response(
                {"message": "Organization Handle Not Found"}, status=206
            )
        organization = get_organization_by_domain_handle(domain_handle)
        if not organization:
            return Response(
                {"message": "Organization Not Found"}, status=206
            )

        search = request.GET.get("search")
        pilot_type = request.GET.get("type")
        query = Q(owner=organization)

        if pilot_type:
            query = query & Q(type=pilot_type)

        if search and search != "":
            query = query & Q(
                Q(name__icontains=search)
                | Q(handle__icontains=search)
            )

        queryset = Pilot.objects.filter(query).order_by("-modified")
        page = UnpodCustomPagination(
            self.request,
            queryset,
            PilotMenusSerializer,
            kwargs={"context": {"request": request}},
        )
        page = page.get_paginated_response(return_dict=True)

        return Response(
            {**page, "message": "Pilots Menu List Fetch Successfully"}, status=200
        )

    def update_reaction(self, request, *args, **kwargs):
        handle = kwargs.get("handle")
        pilot_obj = Pilot.objects.filter(handle=handle).only("id").first()
        ser = PostReactionCreate(data=request.data)
        if ser.is_valid():
            validated_data = ser.validated_data
            reaction_count = validated_data.get("reaction_count")
            reactionObj = ThreadPostReaction.objects.create(
                user_id=request.user.id,
                object_id=str(pilot_obj.id),
                object_type="pilot",
                reaction_count=reaction_count,
                reaction_type=validated_data["reaction_type"],
            )
            Pilot.objects.filter(id=pilot_obj.id).update(
                reaction_count=F("reaction_count") + reaction_count
            )
            return Response(
                {
                    "message": "",
                    "data": {"reaction": True, "reaction_count": reaction_count},
                },
                status=200,
            )
        return Response(
            {"message": "There is some Validation error", "errors": ser.errors},
            status=206,
        )

    def reaction_info(self, request, *args, **kwargs):
        handle = kwargs.get("handle")
        pilot_obj = Pilot.objects.filter(handle=handle).only("id").first()
        if not pilot_obj:
            return Response({"message": "Invalid Pilot handle"}, status=206)
        reactionObj = (
            ThreadPostReaction.objects.filter(
                user_id=request.user.id,
                object_id=str(pilot_obj.id),
                object_type="pilot",
            )
            .values("reaction_type", "reaction_at")
            .first()
        )
        resData = {"reaction": reactionObj is not None, **(reactionObj or {})}
        return Response(
            {"message": "Reaction Info Fetch Successfully", "data": resData}, status=200
        )

    def destroy(self, request, *args, **kwargs):
        handle = kwargs.get("handle")
        pilot_obj = Pilot.objects.filter(handle=handle).first()
        if not pilot_obj:
            return Response({"message": "Pilot Not Found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            pilot_obj.delete()
            return Response({"message": "Pilot Deleted Successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"message": f"Error deleting pilot: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def create_pilot(self, request, *args, **kwargs):
        domain_handle = request.headers.get("Org-Handle", None)
        if not domain_handle:
            return Response(
                {"message": "Organization Handle Not Found"}, status=206
            )

        organization = get_organization_by_domain_handle(domain_handle)
        if not organization:
            return Response(
                {"message": "Organization Not Found"}, status=206
            )

        try:
            quality_flag = json.loads(request.data.get('telephony_config')).get('quality')
        except:
            quality_flag = None

        if quality_flag == 'high':
            res = check_for_vapi(request.data)
            if res.get("success"):
                updated_data = res.get("data")
            else:
                return Response(
                    {"error": res.get("error"), "data": request.data},
                    status=status.HTTP_206_PARTIAL_CONTENT
                )
        else:
            updated_data = request.data

        serializer = PilotSerializer(data=updated_data, context={"request": request})

        if serializer.is_valid(raise_exception=True):
            pilot = serializer.save()

            if not organization.pilot:
                organization.pilot = pilot
                organization.save()

                pilot.is_root_identity = True
                pilot.save()

            if pilot.state in ["published"]:
                core_utils.prepare_push_agent(pilot)

            return Response(
                {
                    "message": "Pilot Created Successfully",
                    "data": PilotFullSerializer(
                        pilot, context={"request": request}
                    ).data,
                },
                status=200,
            )

        if not serializer.is_valid():
            print(serializer.errors)

        return Response({"message": "Pilot Creation Failed"}, status=206)

    def retrieve(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise APIException401(
                {"message": "Unauthorized access"}
            )
        handle = kwargs.get("handle")
        pilot_obj = Pilot.objects.filter(handle=handle).select_related(
            'owner',
            'llm_model',
            'llm_model__provider',
            'embedding_model',
            'template',
        ).prefetch_related(
            'pilot_links',
            'numbers',
            'tags',
        ).first()
        if not pilot_obj:
            return Response({"message": "Pilot Not Found"}, status=206)
        if pilot_obj.privacy_type != PrivacyType.public.name:
            if not request.user.is_authenticated:
                return Response(
                    {"message": "Please First Login to View this pilot"}, status=206
                )
        from unpod.core_components.serializers import PilotFullSerializer
        serializer = PilotFullSerializer(pilot_obj, context={"request": request})
        return Response(
            {"message": "Pilot Fetch Successfully", "data": serializer.data}, status=200
        )

    def update_pilot(self, request, *args, **kwargs):
        handle = kwargs.get("handle", None)
        remove_from_redis(f"model_config:{handle}")
        domain_handle = request.headers.get("Org-Handle", None)
        if not domain_handle:
            return Response(
                {"message": "Organization Handle Not Found"}, status=206
            )

        organization = get_organization_by_domain_handle(domain_handle)
        if not organization:
            return Response(
                {"message": "Organization Not Found"}, status=206
            )

        try:
            quality_flag = json.loads(request.data.get('telephony_config')).get('quality')
        except:
            quality_flag = None

        pilot_obj = Pilot.objects.filter(handle=handle).first()
        if not pilot_obj:
            return Response({"message": "Pilot Not Found"}, status=206)

        if organization != pilot_obj.owner:
            return Response(
                {"message": "You are not allowed to update this pilot"},
                status=403  # 403 Forbidden is more appropriate than 206
            )
        try:
            if not quality_flag:
                config = pilot_obj.telephony_config
                quality_flag = config.get('quality')

        except Exception as e:
            print(str(e))

        if quality_flag == 'high':
            res = check_for_vapi(data=request.data, llm_slug=pilot_obj.llm_model, pilot=pilot_obj)
            if res.get("success"):
                updated_data = res.get("data")
            else:
                return Response(
                    {"error": res.get("error"), "data": request.data},
                    status=status.HTTP_206_PARTIAL_CONTENT
                )

        else:
            updated_data = request.data

        serializer = PilotSerializer(pilot_obj, data=updated_data, context={"request": request}, partial=True)

        # till here
        if serializer.is_valid(raise_exception=True):
            pilot = serializer.save()

            if not organization.pilot or (organization.pilot and organization.pilot.handle == pilot.handle):
                organization.pilot = pilot
                telephony = pilot.telephony_config.get("telephony", None)

                if telephony and len(telephony) > 0:
                    number = telephony[0]
                    organization.telephony_number = f"{number.get('country_code', '')}{number.get('number', '')}"

                organization.save()
                pilot.is_root_identity = True
                pilot.save()

            if pilot.state in ["published"]:
                core_utils.prepare_push_agent(pilot)

            return Response(
                {
                    "message": "Pilot Updated Successfully",
                    "data": PilotFullSerializer(
                        pilot_obj,
                        context={"request": request},
                    ).data,
                },
                status=200,
            )
        return Response({"message": "Pilot Update Failed"}, status=206)

    def org_pilot_list(self, request, *args, **kwargs):
        domain = request.GET.get("domain")
        domain_handle_header = request.headers.get("Org-Handle", None)
        domain = domain or domain_handle_header
        if not domain:
            return Response({"message": "Organization Handle Not Found"}, status=206)
        search = request.GET.get("search")
        pilot_type = request.GET.get("type", PilotTypes.Pilot.name)
        org = SpaceOrganization.objects.filter(domain_handle=domain).first()
        if not org:
            return Response({"message": "Organization Not Found"}, status=206)
        query = Q(privacy_type="public", state="published")
        query &= Q(owner=org)
        pilot_type = request.GET.get("type", PilotTypes.Pilot.name)
        if pilot_type:
            query = query & Q(type=pilot_type)
        if search and search != "":
            query = query & Q(
                Q(name__icontains=search)
                | Q(handle__icontains=search)
            )
        queryset = Pilot.objects.filter(query).order_by("-modified")
        page = UnpodCustomPagination(
            self.request,
            queryset,
            PilotListSerializer,
            kwargs={"context": {"request": request}},
        )
        page = page.get_paginated_response(return_dict=True)
        return Response(
            {**page, "message": "Org based pilots list fetch successfully"}, status=200
        )

    def unlink_space(self, request, handle):
        pilot = Pilot.objects.filter(handle=handle).first()
        if not pilot:
            return Response({"message": "Pilot Not Found"}, status=206)

        pilot.space = None
        pilot.save()

        return Response(
            {
                "message": "Pilot unlinked from space successfully",
            }, status=200
        )

    def clone_pilot(self, request, *args, **kwargs):
        handle = kwargs.get("handle")
        name = request.data.get("name")
        domain_handle = self.request.headers.get("Org-Handle", None)
        organization = get_organization_by_domain_handle(domain_handle)

        try:
            pilot = Pilot.objects.filter(handle=handle).first()
            if not pilot:
                return Response({"message": "Pilot Not Found"}, status=206)

            tags = list(pilot.tags.values_list("name", flat=True))  # Load tags to avoid issues after pk=None
            numbers = list(pilot.numbers.values_list("id", flat=True))

            pilot.name = name or f"Copy of {pilot.name}"
            pilot.pk = None
            pilot.handle = f"{pilot.handle}-{generate_uuid()[:10]}"
            pilot.owner = organization
            pilot.created_by = request.user.id
            pilot.save()

            # Add all tags
            PilotService.process_pilot_tags(pilot, tags)

            # Add all numbers
            pilot.numbers.add(*numbers)

            # blocks = Block.objects.filter(superbook__handle=handle)
            # for block in blocks:
            #     block.pk = None
            #     block.pilot = pilot
            #     block.save()

            forms = DynamicForm.objects.filter(type="component", parent_type="agent", status="active")
            for form in forms:
                form_values = DynamicFormValues.objects.filter(form=form, parent_type="agent", parent_id=handle).first()
                if form_values:
                    form_values.pk = None
                    form_values.parent_id = pilot.handle
                    form_values.save()

            return Response(
                {
                    "message": "Pilot Cloned Successfully",
                    "data": PilotFullSerializer(
                        pilot, context={"request": request}
                    ).data,
                },
                status=200,
            )
        except Exception as e:
            return Response(
                {"message": f"Pilot Cloning Failed: {str(e)}"}, status=206
            )

    def export_details(self, request, *args, **kwargs):
        handle = kwargs.get("handle")
        pilot = Pilot.objects.filter(handle=handle).first()
        if not pilot:
            return Response({"message": "Pilot Not Found"}, status=206)

        serializer = PilotExportSerializer(pilot, context={"request": request})
        return Response(
            {
                "message": "Pilot Details Exported Successfully",
                "data": serializer.data,
            },
            status=200,
        )


class PluginViewSet(viewsets.GenericViewSet):
    serializer_class = PluginSerializer
    renderer_classes = [UnpodJSONRenderer]
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        query = Q(privacy_type=PrivacyType.public.value)

        domain = request.GET.get("domain")
        domain_handle_header = request.headers.get("Org-Handle", None)

        if domain:
            org = SpaceOrganization.objects.filter(domain_handle=domain).first()
            query |= Q(owner=org)
        elif domain_handle_header:
            org = SpaceOrganization.objects.filter(
                domain_handle=domain_handle_header
            ).first()
            query |= Q(owner=org)

        queryset = Plugin.objects.filter(query).order_by("-id")
        plugins = PluginSerializer(queryset, many=True)
        return Response(
            {"data": plugins.data, "message": "Plugins List Fetch Successfully"},
            status=200,
        )


class KBViewSet(viewsets.GenericViewSet):
    serializer_class = KBSerializer
    renderer_classes = [UnpodJSONRenderer]
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        query = Q(
            privacy_type=PrivacyType.public.value,
        )

        domain = request.GET.get("domain")
        domain_handle_header = request.headers.get("Org-Handle", None)
        if domain:
            org = SpaceOrganization.objects.filter(domain_handle=domain).first()
            query |= Q(space_organization=org)
        elif domain_handle_header:
            org = SpaceOrganization.objects.filter(
                domain_handle=domain_handle_header
            ).first()
            query |= Q(space_organization=org)

        queryset = (
            Space.objects.filter(space_type=SpaceType.knowledge_base.value)
            .filter(query)
            .order_by("-id")
        )
        kbs = KBSerializer(queryset, many=True)
        return Response(
            {"data": kbs.data, "message": "Knowledge Base List Fetch Successfully"},
            status=200,
        )


class ModelViewSet(viewsets.GenericViewSet):
    serializer_class = ModelSerializer
    renderer_classes = [UnpodJSONRenderer]
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        model_type = request.GET.get("type", "chat")
        queryset = Model.objects.filter(model_type=model_type, status="active")
        models = ModelSerializer(queryset, many=True)
        return Response(
            {"data": models.data, "message": "Models List Fetch Successfully"},
            status=200,
        )

    def provider_models_list(self, request, *args, **kwargs):
        provider = kwargs.get("provider_id")
        model_type = self.request.query_params.get("model_type")

        if not provider:
            return Response({"message": "Provider is required"}, status=206)

        queryset = Model.objects.filter(provider_id=provider, status="active", model_types__code=model_type)
        models = ModelSerializer(queryset, many=True)

        if not models.data:
            return Response(
                {"message": "No models found for the specified provider"}, status=206
            )

        return Response(
            {"data": models.data, "message": "Models List Fetch Successfully"},
            status=200,
        )


class TagViewSet(viewsets.GenericViewSet):
    serializer_class = TagSerializer
    renderer_classes = [UnpodJSONRenderer]
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        queryset = Tag.objects.all()
        models = TagSerializer(queryset, many=True)
        return Response(
            {"data": models.data, "message": "Tags List Fetch Successfully"}, status=200
        )


class GenerateAIPersona(viewsets.GenericViewSet):
    queryset = PilotTemplate.objects.all()
    renderer_classes = [UnpodJSONRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            params = request.GET.dict()
            required_params = ["identity_name", "purpose", "template"]

            errors = []
            for key in required_params:
                if key not in params or not params[key]:
                    errors.append(f"{key} is required")
            if errors:
                return Response(
                    {"success": False, "data": [], "message": ", ".join(errors)},
                    status=500,
                )

            template_slug = params.get("template")
            template = PilotTemplate.objects.filter(slug=template_slug).first()
            if not template:
                return Response({"message": "Template not found"}, status=404)

            headers = {"Authorization": request.headers.get("Authorization")}
            hit = requests.post(
                url=f"{settings.API_SERVICE_URL}/agent/generate-ai-persona/",
                headers=headers,
                json=params,
            )

            if hit:
                data = json.loads(hit.content)
                return Response({"data": data.get("data")}, status=200)

            return Response({"message": "Persona not generated"}, status=206)
        except Exception as e:
            return Response({"message": "Something went wrong"}, status=500)

    def generate_ai_persona(self, request, *args, **kwargs):
        try:
            postData = request.data
            request_data = postData.get("data", None)
            template_slug = postData.get("template", None)
            if not request_data:
                return Response(
                    {"success": False, "data": [], "message": "Data is required"},
                    status=206,
                )

            if not template_slug:
                return Response(
                    {"success": False, "data": [], "message": "Template is required"},
                    status=206,
                )

            template = PilotTemplate.objects.filter(slug=template_slug).first()
            if not template:
                return Response({"message": "Template not found"}, status=404)

            payload = {
                "data": request_data,
                "template": template_slug,
            }

            headers = {"Authorization": request.headers.get("Authorization")}
            hit = requests.post(
                url=f"{settings.API_SERVICE_URL}/agent/generate-ai-persona/",
                headers=headers,
                json=payload,
            )

            if hit:
                data = json.loads(hit.content)
                return Response({"data": data.get("data")}, status=200)

            return Response({"message": "Persona not generated"}, status=206)
        except Exception as e:
            return Response({"message": "Something went wrong"}, status=500)


class PilotPermissionViewSet(viewsets.GenericViewSet):
    renderer_classes = [UnpodJSONRenderer]
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self, permission_type):
        if permission_type == "user":
            return PilotPermissionSerializer
        return PilotPermissionSerializer

    def post(self, request, *args, **kwargs):
        handle = kwargs.get("handle")
        pilot_obj = Pilot.objects.filter(handle=handle).first()

        if not pilot_obj:
            return Response({"message": "Pilot Not Found"}, status=206)

        permission = core_utils.get_user_pilot_permission(pilot_obj, self.request.user)
        if permission not in [RoleCodes.owner.name, RoleCodes.editor.name]:
            return Response(
                {"message": "You are not allowed to add permission"}, status=206
            )

        permission_type = request.data.get("permission_type", "user")
        serializer_class = self.get_serializer_class(permission_type)
        serializer = serializer_class(
            data=request.data, context={"request": request, "pilot": pilot_obj}
        )
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(
                {"message": "Pilot Shared Successfully", "data": serializer.data},
                status=200,
            )

    def update(self, request, *args, **kwargs):
        handle = kwargs.get("handle")
        pilot_link = PilotLink.objects.filter(handle=handle).first()

        if not pilot_link:
            return Response({"message": "Permision Not Found"}, status=206)

        permission = core_utils.get_user_pilot_permission(
            pilot_link.pilot, self.request.user
        )
        if permission not in [RoleCodes.owner.name, RoleCodes.editor.name]:
            return Response(
                {"message": "You are not allowed to add permission"}, status=206
            )

        permission_type = request.data.get("permission_type", "user")
        serializer_class = self.get_serializer_class(permission_type)
        serializer = serializer_class(
            pilot_link,
            data=request.data,
            context={"request": request, "pilot": pilot_link.pilot},
        )
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(
                {
                    "message": "Pilot Permission Updated Successfully",
                    "data": serializer.data,
                },
                status=200,
            )


class RelevantTagLinkCreateView(viewsets.GenericViewSet):
    renderer_classes = [UnpodJSONRenderer]

    def get_permissions(self):
        if self.action == "bulk_create":
            return [AllowAny()]
        return [IsAuthenticated()]

    def post(self, request):
        name = request.data.get('name')
        description = request.data.get('description', '')
        tag_type = request.data.get('type')
        content_type_model = request.data.get('content_type_model')
        object_slug = request.data.get('slug')

        try:
            # Get the content type and model
            content_type = ContentType.objects.get(model=content_type_model.lower())
            model_class = content_type.model_class()
            obj = model_class.objects.get(slug=object_slug)

            # Get or create the tag
            tag_slug = slugify(name)
            tag, _ = RelevantTag.objects.get_or_create(
                slug=tag_slug,
                defaults={'name': name}
            )

            # check if relevant tag link already exists
            if RelevantTagLink.objects.filter(
                tag=tag,
                content_type=content_type,
                object_id=obj.id
            ).exists():
                return Response({
                    'message': 'Label Already Exists'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Get or create the tag link with description
            tag_link, created = RelevantTagLink.objects.get_or_create(
                tag=tag,
                content_type=content_type,
                object_id=obj.id,
                type=tag_type,
                defaults={'description': description}
            )

            return Response({
                'message': 'Label Created Successfully',
                'created': created
            }, status=status.HTTP_201_CREATED)

        except ContentType.DoesNotExist:
            return Response({
                'error': f'Content type {content_type_model} does not exist'
            }, status=status.HTTP_400_BAD_REQUEST)
        except model_class.DoesNotExist:
            return Response({
                'error': f'Object with slug {object_slug} does not exist'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        name = request.data.get('name')
        description = request.data.get('description', '')
        tag_type = request.data.get('type')
        content_type_model = request.data.get('content_type_model')
        object_slug = request.data.get('slug')
        old_slug = request.data.get('old-slug')

        try:
            if not old_slug:
                return Response({
                    'error': 'Invalid Request - Old Label Missing'
                }, status=status.HTTP_400_BAD_REQUEST)

            tag_slug = slugify(name)

            # Get the content type and model
            content_type = ContentType.objects.get(model=content_type_model.lower())
            model_class = content_type.model_class()
            obj = model_class.objects.get(slug=object_slug)

            # check if old  tag link exists
            if not RelevantTagLink.objects.filter(
                tag__slug=old_slug,
                content_type=content_type,
                object_id=obj.id
            ).exists():
                return Response({
                    'error': 'Label Does not Exist.'
                }, status=status.HTTP_400_BAD_REQUEST)

            if old_slug == tag_slug:
                # Update the existing tag link

                update_tag = RelevantTag.objects.get(
                    slug=old_slug
                )
                update_tag.name = name
                update_tag.save()

                tag_link = RelevantTagLink.objects.get(
                    tag__slug=old_slug,
                    content_type=content_type,
                    object_id=obj.id
                )
                tag_link.description = description
                tag_link.type = tag_type
                tag_link.save()
            else:
                # Get or create the tag
                tag, _ = RelevantTag.objects.get_or_create(
                    slug=tag_slug,
                    defaults={'name': name}
                )

                # check if relevant tag link already exists
                if RelevantTagLink.objects.filter(
                    tag=tag,
                    content_type=content_type,
                    object_id=obj.id
                ).exists():
                    return Response({
                        'message': 'Edited Label Already Exists'
                    }, status=status.HTTP_400_BAD_REQUEST)

                # remove old relevant tag link
                RelevantTagLink.objects.filter(
                    tag__slug=old_slug,
                    content_type=content_type,
                    object_id=obj.id
                ).delete()

                # Get or create the tag link with description
                tag_link, created = RelevantTagLink.objects.get_or_create(
                    tag=tag,
                    content_type=content_type,
                    object_id=obj.id,
                    type=tag_type,
                    defaults={'description': description}
                )

            return Response({
                'message': 'Label Updated Successfully'
            }, status=status.HTTP_200_OK)

        except ContentType.DoesNotExist:
            return Response({
                'error': f'Invalid Request'
            }, status=status.HTTP_400_BAD_REQUEST)
        except RelevantTagLink.DoesNotExist:
            return Response({
                'error': f'Label Does not Exist.'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    def bulk_create(self, request):
        # Get common parameters
        content_type_model = request.data.get('content_type_model')
        object_slug = request.data.get('slug')
        object_token = request.data.get('token')
        tag_type = request.data.get('type')
        tags = request.data.get('tags', [])  # Array of {name, description} objects

        response_data = {
            'success': [],
            'errors': []
        }

        try:
            obj_query = {}
            if object_token:
                obj_query['token'] = object_token
            if object_slug:
                obj_query['slug'] = object_slug

            # Get the content type and model once
            content_type = ContentType.objects.get(model=content_type_model.lower())
            model_class = content_type.model_class()
            obj = model_class.objects.get(**obj_query)

            for tag_data in tags:
                try:
                    name = tag_data.get('name')
                    description = tag_data.get('description', '')

                    # Get or create the tag
                    tag_slug = slugify(name)
                    tag, _ = RelevantTag.objects.get_or_create(
                        slug=tag_slug,
                        defaults={'name': name}
                    )

                    # check if relevant tag link already exists
                    if RelevantTagLink.objects.filter(
                        tag=tag,
                        content_type=content_type,
                        object_id=obj.id
                    ).exists():
                        response_data['errors'].append({
                            'name': name,
                            'error': 'Label Already Exists'
                        })
                        continue

                    # Get or create the tag link with description
                    tag_link, created = RelevantTagLink.objects.get_or_create(
                        tag=tag,
                        content_type=content_type,
                        object_id=obj.id,
                        type=tag_type,
                        defaults={'description': description}
                    )

                    response_data['success'].append({
                        'name': name,
                        'message': 'Label Created Successfully'
                    })

                except Exception as e:
                    response_data['errors'].append({
                        'name': name,
                        'error': str(e)
                    })

        except ContentType.DoesNotExist:
            return Response({
                'error': f'Content type {content_type_model} does not exist'
            }, status=status.HTTP_400_BAD_REQUEST)
        except model_class.DoesNotExist:
            return Response({
                'error': f'Object with slug {object_slug} does not exist'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {'data': response_data},
            status=status.HTTP_200_OK
        )


class RelevantTagListView(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        content_type_model = request.GET.get('content_type_model')
        object_slug = request.GET.get('slug')

        try:
            # Get the content type and model
            content_type = ContentType.objects.get(model=content_type_model.lower())
            model_class = content_type.model_class()
            obj = model_class.objects.get(slug=object_slug)

            # Get default tags with descriptions
            query = Q(default_tag_links__content_type=content_type)
            if model_class == Space:
                query = query & Q(default_tag_links__space_content_type=obj.content_type)
            default_tags = RelevantTag.objects.filter(query).annotate(
                description=F('default_tag_links__description')
            ).order_by('default_tag_links__sort_order')

            # Get tags linked to the object with descriptions
            object_tags = RelevantTag.objects.filter(
                tag_links__content_type=content_type,
                tag_links__object_id=obj.id
            ).annotate(
                description=F('tag_links__description')
            ).order_by('tag_links__sort_order')

            return Response({
                'default_tags': RelevantTagSerializer(default_tags, many=True).data,
                'object_tags': RelevantTagSerializer(object_tags, many=True).data
            })

        except (ContentType.DoesNotExist, model_class.DoesNotExist):
            return Response({
                'default_tags': [],
                'object_tags': []
            })
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class RelevantTagLinkDeleteView(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        content_type_model = request.data.get('content_type_model')
        object_slug = request.data.get('slug')
        tag_slug = request.data.get('tag_slug')

        try:
            # Get the content type and model
            content_type = ContentType.objects.get(model=content_type_model.lower())
            model_class = content_type.model_class()
            obj = model_class.objects.get(slug=object_slug)

            # Get the tag
            tag = RelevantTag.objects.get(slug=tag_slug)

            # Delete the tag link
            RelevantTagLink.objects.filter(
                tag=tag,
                content_type=content_type,
                object_id=obj.id
            ).delete()

            return Response({
                'message': 'Label Deleted Successfully'
            }, status=status.HTTP_200_OK)

        except ContentType.DoesNotExist:
            return Response({
                'error': f'Invalid Request - Content Type Does not Exists'
            }, status=status.HTTP_400_BAD_REQUEST)
        except model_class.DoesNotExist:
            return Response({
                'error': f'Invalid Request - Object Does not Exists'
            }, status=status.HTTP_400_BAD_REQUEST)
        except RelevantTag.DoesNotExist:
            return Response({
                'error': f'Label Does Not Exists'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class VoiceProfilesViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    renderer_classes = [UnpodJSONRenderer]

    def get(self, request):
        voice_profiles = VoiceProfiles.objects.filter(status=ModelBasicStatus.active.name)
        serializer = VoiceProfilesRetrieveSerializer(voice_profiles, many=True)
        data = serializer.data
        if data:
            return Response({"data": data}, status=status.HTTP_200_OK)

        return Response({"message": "No voice profiles found", "data": []}, status=status.HTTP_200_OK)

    def post(self, request):
        try:
            data = request.data.copy()
            tts_languages = data.pop("tts_language", [])
            if isinstance(tts_languages, str):
                tts_languages = [tts_languages]

            stt_languages = data.pop("stt_language", [])
            if isinstance(stt_languages, str):
                stt_languages = [stt_languages]

            tts_language_objs = Language.objects.filter(code__in=[code.lower() for code in tts_languages])
            stt_language_objs = Language.objects.filter(code__in=[code.lower() for code in stt_languages])
            llm = Model.objects.filter(name=data["llm_model"], provider__model_type="LLM").first()
            stt = Model.objects.filter(name=data["stt_model"], provider__model_type="Transcriber").first()
            tts = Model.objects.filter(name=data["tts_model"], provider__model_type="Voice").first()
            voice = Voice.objects.filter(name=data["tts_voice"]).first()

            if voice.provider.id == data["tts_provider"]:
                data["tts_voice"] = voice.id
            else:
                return Response({"message": "voice is not valid for the given provider"},
                                status=status.HTTP_400_BAD_REQUEST)

            if llm and stt and tts:
                data["llm_model"] = llm.id
                data["stt_model"] = stt.id
                data["tts_model"] = tts.id
            else:
                return Response({
                    "message": "model has an invalid value couldn't get the id"
                })

            serializer = VoiceProfilesSerializer(data=data)

            if serializer.is_valid():
                instance = serializer.save()
                if tts_language_objs.exists():
                    instance.tts_language.set(tts_language_objs)
                if stt_language_objs.exists():
                    instance.stt_language.set(stt_language_objs)
                return Response({
                    "data": VoiceProfilesRetrieveSerializer(instance).data
                }, status=status.HTTP_201_CREATED)

            return Response({
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as ex:
            return Response({
                "message": str(ex)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, profile_id):
        voice_profile = VoiceProfiles.objects.get(pk=profile_id)
        serializer = VoiceProfilesSerializer(voice_profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def fetch(self, request, profile_id):
        try:
            voice_profile = VoiceProfiles.objects.get(pk=profile_id)
            serializer = VoiceProfilesRetrieveSerializer(voice_profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except VoiceProfiles.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)


class VoicesViewSet(viewsets.GenericViewSet):
    permission_classes = []

    def get_profile_voice(self, request, profile_id):
        profile = VoiceProfiles.objects.filter(agent_profile_id=profile_id).first()

        if not profile:
            return HttpResponse("Voice Profile not found", content_type="text/plain", status=404)

        voice_id = profile.tts_voice.code
        voice_name = profile.tts_voice.name
        provider = profile.tts_voice.provider.name.lower()
        gender = profile.gender
        greeting_message = profile.greeting_message  # Get greeting_message from voice profile
        languages = profile.tts_language.all()  # Fixed: use tts_language instead of stt_language
        languages_codes = [lang.code for lang in languages]
        language = '_'.join(languages_codes) if languages_codes else None

        return self.get_voice(voice_id, provider, gender, language, voice_name, greeting_message)

    def get_voice_media(self, request, voice_id, provider):
        if provider.isdigit():
            provider = Provider.objects.get(id=provider).name.lower()
        else:
            provider = provider.lower()

        gender = None
        voice_name = None
        profile_id = request.GET.get("profile_id")
        if profile_id:
            voice_profile = VoiceProfiles.objects.filter(agent_profile_id=profile_id).first()
            if voice_profile:
                gender = voice_profile.gender

        if not gender:
            gender = request.GET.get("gender", "F")
        gender = gender.upper()

        language = request.GET.get("language")
        voice = Voice.objects.filter(code=voice_id).first()
        if not voice and len(voice_id) == 32:
            # voice_id without hyphens, try adding them (UUID format)
            formatted_id = f"{voice_id[:8]}-{voice_id[8:12]}-{voice_id[12:16]}-{voice_id[16:20]}-{voice_id[20:]}"
            voice = Voice.objects.filter(code=formatted_id).first()
        elif not voice and len(voice_id) == 36 and '-' in voice_id:
            # voice_id with hyphens, try without them
            voice = Voice.objects.filter(code=voice_id.replace('-', '')).first()

        if voice:
            voice_name = voice.name

        return self.get_voice(voice_id, provider, gender, language, voice_name)

    def get_voice(self, voice_id, provider, gender, language, voice_name=None, greeting_message=None):
        # Use voice_name for display in sample text, fallback to voice_id if not provided
        display_name = voice_name or voice_id

        # Provider language capabilities (default if not specified)
        provider_language_map = {
            "sarvam": "hi",           # Hindi only
            "elevenlabs": "en_hi",    # Multilingual
            "lmnt": "en",             # English only
            "cartesia": "en_hi",      # Multilingual
            "inworld": "en_hi",       # Multilingual
            "google": "en_hi",        # Multilingual
            "openai": "en",           # English only
            "deepgram": "en",         # English only
            "groq": "en",             # English only
            "unpod": "en_hi",         # Multilingual (uses Cartesia)
        }

        # Process language - always run this regardless of greeting_message
        if not language:
            language = provider_language_map.get(provider, "en")
        language = language.lower()

        # If greeting_message is provided from voice profile, use it directly
        if greeting_message:
            text = greeting_message
        else:
            # Fallback to default text samples
            # Gender-specific help text for each Indian language
            help_text = {
                "hi": "मैं आपकी कैसे मदद कर सकता हूं?" if gender == "M" else "मैं आपकी कैसे मदद कर सकती हूं?",
                "bn": "আমি আপনাকে কিভাবে সাহায্য করতে পারি?",
                "ta": "நான் உங்களுக்கு எப்படி உதவ முடியும்?",
                "te": "నేను మీకు ఎలా సహాయం చేయగలను?",
                "mr": "मी तुम्हाला कशी मदत करू शकतो?" if gender == "M" else "मी तुम्हाला कशी मदत करू शकते?",
                "gu": "હું તમને કેવી રીતે મદદ કરી શકું?",
                "kn": "ನಾನು ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಬಹುದು?",
                "ml": "എനിക്ക് നിങ്ങളെ എങ്ങനെ സഹായിക്കാനാകും?",
                "pa": "ਮੈਂ ਤੁਹਾਡੀ ਕਿਵੇਂ ਮਦਦ ਕਰ ਸਕਦਾ ਹਾਂ?" if gender == "M" else "ਮੈਂ ਤੁਹਾਡੀ ਕਿਵੇਂ ਮਦਦ ਕਰ ਸਕਦੀ ਹਾਂ?",
                "or": "ମୁଁ ଆପଣଙ୍କୁ କିପରି ସାହାଯ୍ୟ କରିପାରିବି?",
            }

            text_samples = {
                # English
                "en": f"Hello, how are you doing? I am {display_name}",

                # Hindi
                "hi": f"नमस्ते, आप कैसे हैं? मैं {display_name} हूं। {help_text['hi']}",

                # Bengali
                "bn": f"নমস্কার, আপনি কেমন আছেন? আমি {display_name}। {help_text['bn']}",

                # Tamil
                "ta": f"வணக்கம், நீங்கள் எப்படி இருக்கிறீர்கள்? நான் {display_name}. {help_text['ta']}",

                # Telugu
                "te": f"నమస్కారం, మీరు ఎలా ఉన్నారు? నేను {display_name}. {help_text['te']}",

                # Marathi
                "mr": f"नमस्कार, तुम्ही कसे आहात? मी {display_name} आहे. {help_text['mr']}",

                # Gujarati
                "gu": f"નમસ્તે, તમે કેમ છો? હું {display_name} છું. {help_text['gu']}",

                # Kannada
                "kn": f"ನಮಸ್ಕಾರ, ನೀವು ಹೇಗಿದ್ದೀರಿ? ನಾನು {display_name}. {help_text['kn']}",

                # Malayalam
                "ml": f"നമസ്കാരം, നിങ്ങൾ എങ്ങനെയിരിക്കുന്നു? ഞാൻ {display_name} ആണ്. {help_text['ml']}",

                # Punjabi
                "pa": f"ਸਤ ਸ੍ਰੀ ਅਕਾਲ, ਤੁਸੀਂ ਕਿਵੇਂ ਹੋ? ਮੈਂ {display_name} ਹਾਂ। {help_text['pa']}",

                # Odia
                "or": f"ନମସ୍କାର, ଆପଣ କେମିତି ଅଛନ୍ତି? ମୁଁ {display_name}। {help_text['or']}",

                # Multilingual (English + Indian language mix)
                "en_hi": f"Hello, how are you doing? नमस्ते, आप कैसे हैं? I am {display_name}. {help_text['hi']}",
                "en_bn": f"Hello, how are you doing? নমস্কার, আপনি কেমন আছেন? I am {display_name}. {help_text['bn']}",
                "en_ta": f"Hello, how are you doing? வணக்கம், நீங்கள் எப்படி இருக்கிறீர்கள்? I am {display_name}. {help_text['ta']}",
                "en_te": f"Hello, how are you doing? నమస్కారం, మీరు ఎలా ఉన్నారు? I am {display_name}. {help_text['te']}",
                "en_mr": f"Hello, how are you doing? नमस्कार, तुम्ही कसे आहात? I am {display_name}. {help_text['mr']}",
                "en_gu": f"Hello, how are you doing? નમસ્તે, તમે કેમ છો? I am {display_name}. {help_text['gu']}",
                "en_kn": f"Hello, how are you doing? ನಮಸ್ಕಾರ, ನೀವು ಹೇಗಿದ್ದೀರಿ? I am {display_name}. {help_text['kn']}",
                "en_ml": f"Hello, how are you doing? നമസ്കാരം, നിങ്ങൾ എങ്ങനെയിരിക്കുന്നു? I am {display_name}. {help_text['ml']}",
                "en_pa": f"Hello, how are you doing? ਸਤ ਸ੍ਰੀ ਅਕਾਲ, ਤੁਸੀਂ ਕਿਵੇਂ ਹੋ? I am {display_name}. {help_text['pa']}",
                "en_or": f"Hello, how are you doing? ନମସ୍କାର, ଆପଣ କେମିତି ଅଛନ୍ତି? I am {display_name}. {help_text['or']}",
            }

            text = text_samples.get(language, text_samples["en"])

        print(voice_id, provider, text)
        if provider == "elevenlabs":
            try:
                # ElevenLabs language codes
                elevenlabs_language_map = {
                    "en": "en",
                    "hi": "hi",
                    "pa": "pa-IN",   # Punjabi
                    "ta": "ta",      # Tamil
                    "bn": "bn",      # Bengali
                    "te": "te",      # Telugu
                    "ur": "ur",      # Urdu
                    "gu": "gu",      # Gujarati
                    "mr": "mr",      # Marathi
                    "en_hi": "hi",
                    "en_pa": "pa-IN",
                    "en_ta": "ta",
                    "en_bn": "bn",
                    "en_te": "te",
                    "en_ur": "ur",
                    "en_gu": "gu",
                    "en_mr": "mr",
                    "en_ma": "mr",
                }
                elevenlabs_language = elevenlabs_language_map.get(language, "en")

                url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
                headers = {
                    "xi-api-key": settings.ELEVENLABS_API_KEY,
                    "Content-Type": "application/json"
                }
                payload = {
                    "text": text,
                    "model_id": "eleven_multilingual_v2",
                    "language_code": elevenlabs_language
                }
                res = requests.post(url, headers=headers, json=payload)
                res.raise_for_status()
                return HttpResponse(res.content, content_type='audio/mpeg')

            except Exception as e:
                print(f"[ElevenLabs Error]: {e}")
                return HttpResponse(b"Voice not found", content_type="text/plain", status=404)

        elif provider == "cartesia":
            try:
                voice = Voice.objects.filter(code=voice_id).first()
                url = "https://api.cartesia.ai/tts/bytes"
                headers = {
                    "Authorization": f"Bearer {settings.CARTESIA_API_KEY}",
                    "Content-Type": "application/json",
                    "Cartesia-Version": "2025-04-16"
                }
                cartesia_language_map = {
                    "en": "en",
                    "hi": "hi",
                    "pa": "pa",      # Punjabi
                    "ta": "ta",      # Tamil
                    "bn": "bn",      # Bengali
                    "te": "te",      # Telugu
                    "ur": "ur",      # Urdu
                    "gu": "gu",      # Gujarati
                    "mr": "mr",      # Marathi
                    "en_hi": "hi",
                    "en_pa": "pa",
                    "en_ta": "ta",
                    "en_bn": "bn",
                    "en_te": "te",
                    "en_ur": "ur",
                    "en_gu": "gu",
                    "en_mr": "mr",
                    "en_ma": "mr",
                }
                cartesia_language = cartesia_language_map.get(language, "en")
                payload = {
                    "model_id": "sonic-3",
                    "transcript": text,
                    "voice": {
                        "mode": "id",
                        "id": voice.code if voice else "95d51f79-c397-46f9-b49a-23763d3eaa2d"
                    },
                    "output_format": {
                        "container": "mp3",
                        "bit_rate": 128000,
                        "sample_rate": 44100
                    },
                    "language": cartesia_language
                }
                res = requests.post(url, headers=headers, json=payload)
                res.raise_for_status()
                return HttpResponse(res.content, content_type='audio/mpeg')


            except Exception as e:
                print(f"[Cartesia Error]: {e}")
                return HttpResponse(b"Voice not Found", content_type="text/plain", status=500)

        elif provider == "deepgram":
            try:
                url = f"https://api.deepgram.com/v1/speak?model=aura-2-{voice_id.lower()}-en"
                headers = {"Authorization": f"Token {settings.DEEPGRAM_API_KEY}"}
                payload = {"text": text}
                res = requests.post(url, headers=headers, json=payload)
                res.raise_for_status()
                return HttpResponse(res.content, content_type='audio/mpeg')

            except Exception as e:
                print(f"[Deepgram Error]: {e}")
                return HttpResponse(b"Voice not Found", content_type="text/plain", status=500)

        elif provider == "groq":
            try:
                url = "https://api.groq.com/openai/v1/audio/speech"
                headers = {"Authorization": f"Bearer {settings.GROQ_API_KEY}"}
                payload = {
                    "model": "playai-tts",
                    "input": text,
                    "voice": voice_id,
                    "response_format": "mp3"
                }
                res = requests.post(url, headers=headers, json=payload)
                res.raise_for_status()
                return HttpResponse(res.content, content_type='audio/mpeg')

            except Exception as e:
                print(f"[Groq Error]: {e}")
                return HttpResponse(b"Voice not Found", content_type="text/plain", status=500)

        elif provider == "openai":
            try:
                url = "https://api.openai.com/v1/audio/speech"
                headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}"}
                payload = {
                    "model": "gpt-4o-mini-tts",
                    "input": text,
                    "voice": voice_id
                }
                res = requests.post(url, headers=headers, json=payload)
                res.raise_for_status()

                return HttpResponse(res.content, content_type='audio/mpeg')

            except Exception as e:
                print(f"[OpenAI Error]: {e}")
                return HttpResponse(b"Voice not Found", content_type="text/plain", status=500)

        elif provider == "lmnt":
            try:
                url = "https://api.lmnt.com/v1/ai/speech/bytes"
                headers = {
                    "X-API-Key": settings.LMNT_API_KEY,
                    "Content-Type": "application/json"
                }
                # LMNT only supports English text
                lmnt_text = f"Hello, how are you doing? I am {display_name}. How can I help you today?"
                payload = {
                    "text": lmnt_text,
                    "voice": voice_id,
                    "format": "mp3"
                }
                res = requests.post(url, headers=headers, json=payload)
                res.raise_for_status()
                return HttpResponse(res.content, content_type='audio/mpeg')

            except Exception as e:
                print(f"[LMNT Error]: {e}")
                return HttpResponse(b"Voice not Found", content_type="text/plain", status=404)

        elif provider == "sarvam":
            try:
                voice = Voice.objects.filter(code=voice_id).first()
                speaker_code = voice.code if voice else voice_id

                if not text:
                    text = "Hello, this is a test voice from Sarvam AI. How can I help you today?"

                language_code_map = {
                    "hi": "hi-IN",
                    "en": "en-IN",
                    "en_hi": "hi-IN"
                }
                target_language_code = language_code_map.get(language, "en-IN")

                url = "https://api.sarvam.ai/text-to-speech"
                headers = {
                    "api-subscription-key": settings.SARVAM_API_KEY,
                    "Content-Type": "application/json"
                }
                payload = {
                    "text": text,
                    "target_language_code": target_language_code,
                    "speaker": speaker_code,
                    "model": "bulbul:v2"
                }
                res = requests.post(url, headers=headers, json=payload)

                if res.status_code != 200:
                    print(f"[Sarvam API Error] Status: {res.status_code}, Response: {res.text}")
                    return HttpResponse(f"Sarvam API Error: {res.text}".encode(), content_type="text/plain", status=500)

                audio_data = res.json().get("audios", [])
                if audio_data:
                    import base64
                    audio_bytes = base64.b64decode(audio_data[0])
                    return HttpResponse(audio_bytes, content_type='audio/wav')
                return HttpResponse(b"No audio generated", content_type="text/plain", status=500)

            except Exception as e:
                print(f"[Sarvam Error]: {type(e).__name__}: {e}")
                return HttpResponse(f"Sarvam Error: {str(e)}".encode(), content_type="text/plain", status=500)

        elif provider == "google":
            try:
                from google.cloud import texttospeech
                client = texttospeech.TextToSpeechClient()
                synthesis_input = texttospeech.SynthesisInput(text=text)

                language_code_map = {
                    "hi": "hi-IN",
                    "en": "en-US",
                    "en_hi": "hi-IN"
                }
                google_language_code = language_code_map.get(language, "en-US")

                voice_params = texttospeech.VoiceSelectionParams(
                    language_code=google_language_code,
                    name=voice_id
                )
                audio_config = texttospeech.AudioConfig(
                    audio_encoding=texttospeech.AudioEncoding.MP3
                )
                response = client.synthesize_speech(
                    input=synthesis_input,
                    voice=voice_params,
                    audio_config=audio_config
                )
                return HttpResponse(response.audio_content, content_type='audio/mpeg')

            except Exception as e:
                print(f"[Google TTS Error]: {e}")
                return HttpResponse(b"Voice not Found", content_type="text/plain", status=500)

        elif provider == "inworld":
            try:
                import base64
                # Inworld language codes
                inworld_language_map = {
                    "en": "en-US",
                    "hi": "hi-IN",
                    "pa": "pa-IN",   # Punjabi
                    "ta": "ta-IN",   # Tamil
                    "bn": "bn-IN",   # Bengali
                    "te": "te-IN",   # Telugu
                    "ur": "ur-IN",   # Urdu
                    "gu": "gu-IN",   # Gujarati
                    "mr": "mr-IN",   # Marathi
                    "en_hi": "hi-IN",
                    "en_pa": "pa-IN",
                    "en_ta": "ta-IN",
                    "en_bn": "bn-IN",
                    "en_te": "te-IN",
                    "en_ur": "ur-IN",
                    "en_gu": "gu-IN",
                    "en_mr": "mr-IN",
                    "en_ma": "mr-IN",
                }
                inworld_language = inworld_language_map.get(language, "en-US")

                url = "https://api.inworld.ai/tts/v1/voice"
                headers = {
                    "Authorization": f"Basic {settings.INWORLD_API_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "text": text,
                    "voiceId": voice_id,
                    "modelId": "inworld-tts-1",
                    "languageCode": inworld_language,
                    "audioConfig": {
                        "audioEncoding": "MP3",
                        "sampleRateHertz": 44100
                    }
                }
                res = requests.post(url, headers=headers, json=payload)
                res.raise_for_status()
                response_data = res.json()
                audio_base64 = response_data.get("audio") or response_data.get("audioContent") or response_data.get("data")
                if audio_base64:
                    audio_bytes = base64.b64decode(audio_base64)
                    return HttpResponse(audio_bytes, content_type='audio/mpeg')
                return HttpResponse(b"No audio generated", content_type="text/plain", status=500)

            except Exception as e:
                return HttpResponse(b"Voice not Found", content_type="text/plain", status=500)

        elif provider == "unpod":
            try:

                from unpod.core_components.unpod_assistant.Agent_Enum import UNPOD_VOICE_MAP
                voice = Voice.objects.filter(code=voice_id).first()
                url = "https://api.cartesia.ai/tts/bytes"

                headers = {
                    "Authorization": f"Bearer {settings.CARTESIA_API_KEY}",
                    "Content-Type": "application/json",
                    "Cartesia-Version": "2025-04-16"
                }
                payload = {
                    "model_id": "sonic-2-2025-06-11",
                    "transcript": text,
                    "voice": {
                        "mode": "id",
                        "id": UNPOD_VOICE_MAP.get(voice_id,"95d51f79-c397-46f9-b49a-23763d3eaa2d")
                    },
                    "output_format": {
                        "container": "mp3",
                        "bit_rate": 128000,
                        "sample_rate": 44100
                    },
                    "language": "en"
                }
                res = requests.post(url, headers=headers, json=payload)
                res.raise_for_status()
                return HttpResponse(res.content, content_type='audio/mpeg')


            except Exception as e:
                print(f"[Cartesia Error]: {e}")
                return HttpResponse(b"Voice not Found", content_type="text/plain", status=500)
        else:
            return Response({"message": "Voice will be available soon"}, status=status.HTTP_200_OK)


class GlobalSystemConfigViewSet(viewsets.GenericViewSet):
    renderer_classes = [UnpodJSONRenderer]

    def get(self, request):
        data = GlobalSystemConfig.objects.all()
        serializer = GlobalSystemConfigSerializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = GlobalSystemConfigSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PilotTemplateViewSet(viewsets.GenericViewSet):
    """
    ViewSet for Pilot Templates.
    Provides list, retrieve, and category-based filtering.
    """
    renderer_classes = [UnpodJSONRenderer]
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        """
        List all active templates with optional category filter.
        GET /api/v1/core/templates/?category=hr
        """
        category = request.GET.get("category")
        queryset = PilotTemplate.objects.filter(is_active=True)

        if category:
            queryset = queryset.filter(category=category)

        queryset = queryset.order_by('display_order', '-created')

        page = UnpodCustomPagination(
            self.request,
            queryset,
            PilotTemplateListSerializer,
            kwargs={"context": {"request": request}},
        )
        page = page.get_paginated_response(return_dict=True)

        return Response(
            {**page, "message": "Templates fetched successfully"},
            status=status.HTTP_200_OK
        )


class KnowledgebaseEvalsViewSet(viewsets.GenericViewSet):

    renderer_classes = [UnpodJSONRenderer]
    permission_classes = [IsAuthenticated]

    def _validate_request(self, request):
        """Validate and return serializer validated data"""
        serializer = KnowledgebaseEvalsSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data

    def check_create_linked_eval_entity(self, pilot):
        eval_kn_token = []
        old_kn_token = []
        gen_type = "knowledgebase"
        linked_kn_bases = Space.objects.filter(
            pilots__pilot__id=pilot.id, space_type=SpaceType.knowledge_base.name
        ).prefetch_related("spacememberroles_space")
        for kn_base in linked_kn_bases:
            kn_base_token = kn_base.token
            check_evals = self.check_eval_entity("knowledgebase", kn_base_token)
            if not check_evals:
                eval_name = kn_base.name
                eval_name = f"{eval_name} Evals"
                privacy_type = kn_base.privacy_type
                space_organization = kn_base.space_organization
                user_list = kn_base.spacememberroles_space.all().values(
                    "user__id", "role__role_code"
                )
                eval_kn, eval_space = self.create_eval_entity(
                    eval_name,
                    gen_type,
                    kn_base_token,
                    privacy_type,
                    space_organization,
                    user_list,
                )
                eval_kn_token.append(eval_space.token)
            else:
                old_kn_token.append(check_evals.eval_data["space_token"])
        return eval_kn_token, old_kn_token

    def check_eval_entity(self, eval_type, linked_handle):
        check_evals = KnowledgeBaseEvals.objects.filter(
            eval_type=eval_type, linked_handle=linked_handle
        ).first()
        return check_evals

    def create_collection_config(self, eval_token, config_data):
        from unpod.core_components.constants import EVALS_SCHEMA

        config_coll = "collection_config"
        schema_coll = "collection_schema"
        config = MongoDBQueryManager.run_query(
            config_coll, "find_one", {"token": eval_token}
        )
        if not config:
            print("Config not found for token:", eval_token)
            current_time = timezone.now()
            inserted = MongoDBQueryManager.run_query(
                config_coll,
                "insert_one",
                {"created": current_time, "modified": current_time, **config_data},
            )
            collection_id = inserted.inserted_id
            schema_config = {
                "created": current_time,
                "modified": current_time,
                "collection_id": str(collection_id),
                "org_id": config_data["org_id"],
                "token": eval_token,
                "fields": {},
                "keywords": [],
                "schemas": EVALS_SCHEMA,
            }
            inserted = MongoDBQueryManager.run_query(
                schema_coll, "insert_one", schema_config
            )

    def create_eval_entity(
        self,
        eval_name,
        gen_type,
        linked_handle,
        privacy_type,
        space_organization,
        user_list,
    ):
        eval_kn = KnowledgeBaseEvals.objects.create(
            eval_name=eval_name,
            eval_type=gen_type,
            linked_handle=linked_handle,
            gen_status=StatusEnum.pending.name,
        )
        eval_space, created = Space.objects.get_or_create(
            name=f"{eval_name}",
            privacy_type=privacy_type,
            space_type=SpaceType.knowledge_base.name,
            space_organization=space_organization,
            content_type="evals",
            defaults={
                "description": f"Eval Knowledge Base for {eval_name}",
                "created_by": self.request.user.id,
            },
        )
        for user in user_list:
            role_code = user["role__role_code"]
            user_id = user["user__id"]
            createPermission(SpaceMemberRoles, role_code, user_id, space=eval_space)
        KnowledgeBaseEvals.objects.filter(id=eval_kn.id).update(
            eval_data={"space_token": eval_space.token}
        )
        config_data = {
            "org_id": space_organization.id,
            "name": eval_name,
            "desc": eval_name,
            "collection_type": "evals",
            "token": eval_space.token,
        }
        self.create_collection_config(eval_space.token, config_data)
        return eval_kn, eval_space

    def trigger_prefect(self, trigger_data):
        """Trigger Prefect flow with given data"""
        try:
            deployment_name = "Generate-Agent-Evals"
            asyncio.run(trigger_deployment(deployment_name, trigger_data))
        except Exception as e:
            print(f"Prefect flow trigger error: {e}")
            return None

    def generate_evals(self, request, *args, **kwargs):
        """Generate evals for Knowledgebase/Pilot"""
        validated_data = self._validate_request(request)
        gen_type = validated_data["type"]
        kn_token = validated_data.get("kn_token")
        pilot_handle = validated_data.get("pilot_handle")
        pilot = validated_data.get("pilot")
        kn_base = validated_data.get("kn_base")
        force = validated_data.get("force", False)

        trigger_data = {"gen_type": gen_type}
        if kn_base:
            if kn_base.content_type == "evals":
                return Response(
                    {
                        "message": "Cannot generate evals for existing evals knowledge base"
                    },
                    status=206,
                )
        check_evals = self.check_eval_entity(gen_type, kn_token or pilot_handle)
        if check_evals:
            if check_evals.gen_status != StatusEnum.completed.name:
                return Response(
                    {"message": "Evaluation is already in progress"}, status=206
                )
            if check_evals.gen_status == StatusEnum.completed.name and not force:
                return Response(
                    {"message": "Evaluation already generated"},
                    status=206,
                )
            if force:
                # Update status to pending if forcing regeneration
                KnowledgeBaseEvals.objects.filter(id=check_evals.id).update(
                    gen_status=StatusEnum.pending.name
                )
                if kn_token:
                    trigger_data["kn_token"] = kn_token
                if pilot_handle:
                    trigger_data["pilot_handle"] = pilot_handle
                self.trigger_prefect({"job": trigger_data})
                return Response(
                    {"message": "Evaluation generation started"},
                    status=status.HTTP_200_OK,
                )
        else:
            space_tokens = []
            if gen_type == "knowledgebase":
                eval_name = kn_base.name
                eval_name = f"{eval_name} Evals"
                privacy_type = kn_base.privacy_type
                space_organization = kn_base.space_organization
                user_list = kn_base.spacememberroles_space.all().values(
                    "user__id", "role__role_code"
                )
                eval_kn, eval_space = self.create_eval_entity(
                    eval_name,
                    gen_type,
                    kn_token,
                    privacy_type,
                    space_organization,
                    user_list,
                )
                trigger_data["kn_token"] = kn_token
                space_tokens.append(eval_space.token)
            elif gen_type == "pilot":
                eval_name = pilot.name
                eval_name = f"{eval_name} Evals"
                privacy_type = PrivacyType.shared.name
                space_organization = pilot.owner
                user_list = (
                    pilot.owner.organizationmemberroles_organization.all().values(
                        "user__id", "role__role_code"
                    )
                )
                eval_kn, eval_space = self.create_eval_entity(
                    eval_name,
                    gen_type,
                    pilot_handle,
                    privacy_type,
                    space_organization,
                    user_list,
                )
                space_tokens.append(eval_space.token)
                trigger_data["pilot_handle"] = pilot_handle
                eval_kn_token, old_kn_token = self.check_create_linked_eval_entity(
                    pilot
                )
                trigger_data["kn_token"] = ",".join(eval_kn_token + old_kn_token)
                space_tokens.extend(eval_kn_token)
            # Trigger prefect
            self.trigger_prefect({"job": trigger_data})
            spaces = Space.objects.filter(token__in=space_tokens).select_related(
                "space_organization"
            )
            spaces = SpaceListSerializers(
                spaces, many=True, context={"request": request}
            ).data
            return Response(
                {"message": "Evaluation generation started", "data": spaces},
                status=status.HTTP_200_OK,
            )

    def fetch_evals(self, request, *args, **kwargs):
        validated_data = self._validate_request(request)
        gen_type = validated_data["type"]
        kn_token = validated_data.get("kn_token")
        pilot_handle = validated_data.get("pilot_handle")
        check_evals = KnowledgeBaseEvals.objects.filter(
            eval_type=gen_type, linked_handle=kn_token or pilot_handle
        ).first()
        if not check_evals:
            return Response({"message": "Data found", "data": [], "count": -1})
        return Response({"message": "Data found", "data": [], "count": 0})

class UseCasesViewSet(viewsets.GenericViewSet):
    """
    ViewSet for UseCases.
    Provides list of active use cases.
    """

    renderer_classes = [UnpodJSONRenderer]
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
        """
        List all active use cases.
        GET /api/v1/core/use-cases/
        """
        queryset = UseCases.objects.filter(status=ModelBasicStatus.active.name)
        queryset = queryset.order_by("sort_order", "-created")

        serializer = UseCasesSerializer(
            queryset, many=True, context={"request": request}
        )

        return Response(
            {"message": "Use cases fetched successfully", "data": serializer.data},
            status=status.HTTP_200_OK,
        )

class PilotTestViewSet(viewsets.GenericViewSet):
    renderer_classes = [UnpodJSONRenderer]
    permission_classes = [AllowAny]

    def agent_eval_testing(self, request, *args, **kwargs):
        from asgiref.sync import async_to_sync

        agent_id = request.data.get('agent_id')
        kn_bases = request.data.get('kn_bases', [])

        try:
            async_to_sync(trigger_deployment)(
                "Agent-Evals-Test",
                {
                    "agent_id": agent_id,
                    "kn_bases": kn_bases
                },
            )

            return Response(status=status.HTTP_200_OK, data={"message": "Successfully triggered agent evaluation"})

        except Exception as e:

            print(e)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={"message": str(e)})

    def get_test_results(self,request,agent_id):
        if not agent_id:
            return Response(status=status.HTTP_206_PARTIAL_CONTENT)

        try:
            collection_name = "eval_results"
            collection = MongoDBQueryManager.get_collection(collection_name)

            data=list(collection.find(
                {"agent_id": agent_id},
                {"_id":0}
            ))

            return Response({"count": len(data), "data": data}, status=status.HTTP_200_OK)

        except Exception as e:
            print(e)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR,data={"error":str(e)})
