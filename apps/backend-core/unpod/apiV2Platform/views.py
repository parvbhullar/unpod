"""
API v2 Platform ViewSet - MongoDB Direct Access
This ViewSet is specifically for external users and fetches data directly from MongoDB
instead of calling external microservices (unlike API v1).
"""

from django.db.models import Q
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from unpod.apiV2Platform.constants import (
    UnAuthenticatedApiResponse,
    TELEPHONY_NUMBER_EXAMPLE,
    TELEPHONY_NUMBER_BAD_REQUEST_EXAMPLE,
    PROVIDER_LIST_EXAMPLE,
    PROVIDER_CONFIG_RESPONSE_EXAMPLE,
    PROVIDER_CONFIG_VAPI_REQUEST_EXAMPLE,
    PROVIDER_CONFIG_LIVEKIT_REQUEST_EXAMPLE,
    PROVIDER_CONFIG_DAILY_REQUEST_EXAMPLE,
    PROVIDER_CONFIG_UNPOD_REQUEST_EXAMPLE,
    PROVIDER_CONFIG_WEBSOCKET_REQUEST_EXAMPLE,
    PROVIDER_CONFIG_UPDATE_VAPI_REQUEST_EXAMPLE,
    PROVIDER_CONFIG_UPDATE_LIVEKIT_REQUEST_EXAMPLE,
    PROVIDER_CONFIG_UPDATE_DAILY_REQUEST_EXAMPLE,
    PROVIDER_CONFIG_UPDATE_UNPOD_REQUEST_EXAMPLE,
    PROVIDER_CONFIG_UPDATE_WEBSOCKET_REQUEST_EXAMPLE,
    PROVIDER_CONFIG_DELETE_EXAMPLE,
    BRIDGES_LIST_EXAMPLE,
    BRIDGE_DETAIL_EXAMPLE,
    BRIDGE_CREATE_REQUEST_EXAMPLE,
    BRIDGE_CREATE_RESPONSE_EXAMPLE,
    BRIDGE_UPDATE_RESPONSE_EXAMPLE,
    BRIDGE_DELETE_EXAMPLE,
    BRIDGE_CONNECT_PROVIDER_REQUEST_EXAMPLE,
    BRIDGE_DISCONNECT_PROVIDER_REQUEST_EXAMPLE,
    CALL_LOGS_LIST_EXAMPLE,
)
from unpod.common.authentication import UnpodJSONWebTokenAuthentication
from unpod.common.pagination import UnpodCustomPagination
from unpod.common.renderers import UnpodJSONRenderer
from unpod.apiV2Platform.serializers import (
    TaskRunCreateResponseSerializer,
    RunListResponseSerializer,
    TaskDetailResponseSerializer,
    AgentTasksResponseSerializer,
    SpaceTasksResponseSerializer,
    CallLogsResponseSerializer,
    SpaceTaskRunSerializer,
    AssignNumberToBridgeSerializer,
    TelephonyNumberSerializer,
    TelephonyNumberResponseSerializer,
    ProviderResponseSerializer,
    TelephonyProviderSerializer,
    ProviderConfigurationsResponseSerializer,
    ProviderConfigurationResponseSerializer,
    CreateProviderConfigurationSerializer,
    UpdateProviderConfigurationSerializer,
    VoiceBridgeListResponseSerializer,
    VoiceBridgeDetailResponseSerializer,
    CallLogItemSerializer,
    VoiceBridgeListSerializer,
    SpaceListResponseV2Serializer,
    SpaceDetailResponseV2Serializer,
)
from unpod.core_components.models import TelephonyNumber, Provider
from unpod.telephony.serializers import ProviderCredentialSerializer

# Import telephony serializers directly from telephony app
from unpod.telephony.serializers import (
    VoiceBridgeSerializer,
)
from drf_spectacular.utils import (
    OpenApiResponse,
    OpenApiParameter,
)

from unpod.apiV2Platform.utils import (
    fetch_tasks_by_agent,
    fetch_call_logs,
)
from unpod.core_components.tasks.serializers import TaskRunSerializer
from unpod.core_components.tasks.utils import (
    convert_run_data,
    push_to_tasks,
    fetch_space_runs,
    fetch_space_run_tasks,
    fetch_space_tasks,
)
from unpod.space.utils import checkSpaceAccess, checkSpaceOperationAccess
from drf_spectacular.utils import extend_schema


class TaskServiceV2ViewSet(viewsets.GenericViewSet):
    """
    API v2 Platform ViewSet for Task Service
    - Uses MongoDB directly instead of external microservices
    - Designed for external user access
    """

    serializer_class = TaskRunSerializer
    renderer_classes = [UnpodJSONRenderer]
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication, UnpodJSONWebTokenAuthentication]

    @extend_schema(
        tags=["Runs"],
        operation_id="Gets Space Runs",
        responses={
            200: RunListResponseSerializer,
            206: {
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                    "errors": {"type": "string"},
                },
            },
        },
        description="Get all Runs in a Space. Returns a list of all runs with their details including run ID, status, "
        "and associated user information.",
    )
    def get_space_runs(self, request, *args, **kwargs):
        space_token = kwargs.get("space_token")
        space_role = checkSpaceAccess(
            request.user,
            token=space_token,
            check_role=True,
            custom_message="You Don't have Access to this Space, You can't do any operation to this Space",
        )
        checkSpaceOperationAccess(request.user, space_role)
        space = space_role.space
        runs, status, count = fetch_space_runs(space.id, request)
        if status:
            return Response(
                {"message": "Runs Fetched Successfully", "data": runs, "count": count}
            )
        return Response(
            {"message": "Runs Fetch Failed", "errors": runs["message"]},
            status=206,
        )

    @extend_schema(
        tags=["Runs"],
        operation_id="Get Space Run Tasks",
        responses={
            200: OpenApiResponse(
                response=TaskDetailResponseSerializer,
                description="Successfully retrieved detailed task information for the run",
            ),
            206: OpenApiResponse(
                description="Business logic error occurred",
                response={
                    "type": "object",
                    "properties": {
                        "message": {"type": "string"},
                        "errors": {"type": "string"},
                    },
                },
            ),
        },
        description="Get detailed tasks for a specific run. Returns complete task information including input, "
        "output, cost breakdown, transcript, and analysis.",
    )
    def get_run_tasks(self, request, *args, **kwargs):
        space_token = kwargs.get("space_token")
        run_id = kwargs.get("run_id")
        space_role = checkSpaceAccess(
            request.user,
            token=space_token,
            check_role=True,
            custom_message="You Don't have Access to this Space, You can't do any operation to this Space",
        )
        checkSpaceOperationAccess(request.user, space_role)
        space = space_role.space
        tasks, status, count = fetch_space_run_tasks(space.id, run_id, request)

        if status:
            return Response(
                {"message": "Tasks Fetched Successfully", "data": tasks, "count": count}
            )
        return Response(
            {"message": "Runs Fetch Failed", "errors": tasks["message"]},
            status=206,
        )

    @extend_schema(
        tags=["Tasks"],
        operation_id="Get Tasks by Space Token",
        parameters=[
            OpenApiParameter(
                name="space_token",
                location=OpenApiParameter.PATH,
                required=True,
                type=str,
                description="Space token. To get space tokens, use GET /api/v2/platform/spaces/ API.",
            ),
        ],
        responses={
            200: OpenApiResponse(
                response=SpaceTasksResponseSerializer,
                description="Successfully retrieved all tasks for the space with pagination",
            ),
            206: OpenApiResponse(
                description="Tasks fetch failed",
                response={
                    "type": "object",
                    "properties": {
                        "message": {"type": "string"},
                        "errors": {"type": "string"},
                    },
                },
            ),
        },
        description="Fetch all tasks for a specific space using space_token. Supports pagination with page and "
        "page_size query parameters.",
    )
    def get_tasks_by_space_token(self, request, *args, **kwargs):
        space_token = kwargs.get("space_token")

        space_role = checkSpaceAccess(
            request.user,
            token=space_token,
            check_role=True,
            custom_message="You Don't have Access to this Space",
        )
        checkSpaceOperationAccess(request.user, space_role)
        space = space_role.space

        tasks, status, count = fetch_space_tasks(space.id, request)
        if status:
            return Response(
                {"message": "Tasks Fetched Successfully", "data": tasks, "count": count}
            )
        return Response(
            {
                "message": "Tasks Fetch Failed",
                "errors": tasks.get("message", "Unknown error"),
            },
            status=206,
        )

    @extend_schema(
        tags=["Tasks"],
        operation_id="Create Task Run",
        parameters=[
            OpenApiParameter(
                name="space_token",
                location=OpenApiParameter.PATH,
                required=True,
                type=str,
                description="Space token. To get space tokens, use GET /api/v2/platform/spaces/ API.",
            ),
        ],
        request=SpaceTaskRunSerializer,
        responses={
            200: OpenApiResponse(
                response=TaskRunCreateResponseSerializer,
                description="Task created successfully in MongoDB",
            ),
            206: OpenApiResponse(
                description="Validation error or task creation failed",
                response={
                    "type": "object",
                    "properties": {
                        "message": {"type": "string"},
                        "errors": {"type": "string"},
                    },
                },
            ),
        },
        description="Create a Task in a Space",
    )
    def create_space_task(self, request, *args, **kwargs):
        space_token = kwargs.get("space_token")
        space_role = checkSpaceAccess(
            request.user,
            token=space_token,
            check_role=True,
            custom_message="You Don't have Access to this Space, You can't do any operation to this Space",
        )
        checkSpaceOperationAccess(request.user, space_role)
        space = space_role.space
        ser = TaskRunSerializer(data=request.data)
        if ser.is_valid():
            run_data = convert_run_data(
                ser.validated_data, space, request.user, request
            )
            run_push_res, push_status, status_code = push_to_tasks(run_data)
            if push_status:
                return Response(
                    {"message": "Task Created Successfully", "data": run_push_res},
                    status=status_code,
                )
            else:
                return Response(
                    {
                        "message": "Task Creation Failed",
                        "errors": run_push_res["message"],
                    },
                    status=status_code,
                )
        return Response(
            {"message": "There is some Validation error", "errors": ser.errors},
            status=206,
        )

    @extend_schema(
        tags=["Tasks"],
        operation_id="Get Tasks by Agent Handle",
        parameters=[
            OpenApiParameter(
                name="agent_handle",
                location=OpenApiParameter.PATH,
                required=True,
                type=str,
                description="Agent handle. To get agent handles, use GET /api/v2/platform/agents/ API.",
            ),
        ],
        responses={
            200: OpenApiResponse(
                response=AgentTasksResponseSerializer,
                description="Successfully retrieved tasks for the agent",
            ),
            206: OpenApiResponse(
                description="Tasks fetch failed",
                response={
                    "type": "object",
                    "properties": {
                        "message": {"type": "string"},
                        "errors": {"type": "string"},
                    },
                },
            ),
            404: OpenApiResponse(
                description="Agent not found",
                response={
                    "type": "object",
                    "properties": {"message": {"type": "string"}},
                },
            ),
        },
        description="Fetch all tasks assigned to a specific agent/pilot by their handle",
    )
    def get_tasks_by_agent(self, request, *args, **kwargs):
        handle = kwargs.get("agent_handle")

        from unpod.core_components.models import Pilot

        try:
            pilot = Pilot.objects.get(handle=handle)

            if pilot.space:
                space_role = checkSpaceAccess(
                    request.user,
                    space=pilot.space,
                    check_role=True,
                    custom_message="You Don't have Access to this Agent's Space",
                )
        except Pilot.DoesNotExist:
            return Response(
                {"message": "Agent not found"},
                status=404,
            )

        tasks, status, count = fetch_tasks_by_agent(handle, request)
        if status:
            return Response(
                {"message": "Tasks Fetched Successfully", "data": tasks, "count": count}
            )
        return Response(
            {
                "message": "Tasks Fetch Failed",
                "errors": tasks.get("message", "Unknown error"),
            },
            status=206,
        )

    @extend_schema(
        tags=["Tasks"],
        operation_id="List Agents",
        parameters=[
            OpenApiParameter(
                name="Org-Handle",
                location=OpenApiParameter.HEADER,
                required=True,
                type=str,
                description="Organization domain handle. To get Org-Handle, use GET /api/v2/platform/organizations/ API.",
            ),
        ],
        responses={
            200: OpenApiResponse(
                description="List of agents for the organization",
                response={
                    "type": "object",
                    "properties": {
                        "message": {"type": "string"},
                        "count": {"type": "integer"},
                        "data": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "handle": {"type": "string"},
                                    "name": {"type": "string"},
                                    "type": {"type": "string"},
                                    "state": {"type": "string"},
                                },
                            },
                        },
                    },
                },
            ),
            400: OpenApiResponse(description="Org-Handle header missing"),
            401: UnAuthenticatedApiResponse,
            404: OpenApiResponse(description="Organization not found"),
        },
        description="Get all agents (pilots) for an organization. Use the agent handle in /agents/{agent_handle}/tasks/ endpoint.",
    )
    def list_agents(self, request, *args, **kwargs):
        """List all agents for the organization"""
        from unpod.core_components.models import Pilot
        from unpod.space.models import SpaceOrganization

        domain_handle = request.headers.get("Org-Handle", None)
        if not domain_handle:
            return Response(
                {"message": "Organization handle is required in Org-Handle header"},
                status=400,
            )

        # Get organization
        organization = SpaceOrganization.objects.filter(
            domain_handle=domain_handle
        ).first()
        if not organization:
            return Response(
                {"message": "Organization not found"},
                status=404,
            )

        # Get agents for this organization
        agents = Pilot.objects.filter(
            owner=organization,
            state="published",
        ).values("handle", "name", "type", "state", "description", "purpose")

        agent_list = list(agents)

        return Response(
            {
                "message": "Agents fetched successfully",
                "count": len(agent_list),
                "data": agent_list,
            },
            status=200,
        )


class TelephonyNumbersViewSet(viewsets.GenericViewSet):
    """
    API v2 Platform ViewSet for Telephony Numbers
    """

    serializer_class = TelephonyNumberSerializer
    renderer_classes = [UnpodJSONRenderer]
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication, UnpodJSONWebTokenAuthentication]

    @extend_schema(
        tags=["Telephony - Numbers"],
        operation_id="Get Telephony Numbers",
        parameters=[
            OpenApiParameter(
                name="Org-Handle",
                type=str,
                location=OpenApiParameter.HEADER,
                required=True,
                description="Organization domain handle to get assigned numbers",
            ),
        ],
        responses={
            200: OpenApiResponse(
                response=TelephonyNumberResponseSerializer,
                description="Successfully retrieved telephony numbers",
                examples=[TELEPHONY_NUMBER_EXAMPLE],
            ),
            400: OpenApiResponse(
                description="Bad Request",
                response={
                    "type": "object",
                    "properties": {
                        "status_code": {"type": "integer"},
                        "message": {"type": "string"},
                    },
                },
                examples=[TELEPHONY_NUMBER_BAD_REQUEST_EXAMPLE],
            ),
            401: UnAuthenticatedApiResponse,
        },
        description="Get telephony numbers by organization.",
    )
    def get_numbers(self, request, *args, **kwargs):
        """List available telephony numbers"""
        # from unpod.telephony.models import TelephonyNumber

        domain_handle = request.headers.get("Org-Handle", None)
        if not domain_handle:
            Response(
                {
                    "status_code": 400,
                    "message": "Organization handle is required in Org-Handle header",
                },
                status=400,
            )

        queryset = TelephonyNumber.objects.filter(
            active=True, state="NOT_ASSIGNED", agent_number=False
        )

        queryset = queryset.filter(
            Q(organization__domain_handle=domain_handle) | Q(organization__isnull=True)
        )

        serializer = self.get_serializer(queryset, many=True)

        return Response(
            {
                "data": serializer.data,
                "message": "Telephony numbers fetched successfully.",
            },
        )


class TelephonyProvidersViewSet(viewsets.GenericViewSet):
    """
    API v2 Platform ViewSet for Telephony Providers
    """

    serializer_class = TelephonyProviderSerializer
    renderer_classes = [UnpodJSONRenderer]
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication, UnpodJSONWebTokenAuthentication]

    @extend_schema(
        tags=["Telephony - Providers"],
        operation_id="Get Voice Infra Providers",
        responses={
            200: OpenApiResponse(
                response=ProviderResponseSerializer,
                description="Successfully retrieved voice infra providers",
                examples=[PROVIDER_LIST_EXAMPLE],
            ),
            401: UnAuthenticatedApiResponse,
        },
        description="Get all voice infrastructure providers (filtered by type=voice_infra).",
    )
    def get_providers(self, request, *args, **kwargs):
        """List voice infra providers only"""
        # from unpod.telephony.models import Provider

        queryset = Provider.objects.filter(type__iexact="voice_infra")
        serializer = self.get_serializer(queryset, many=True)

        return Response(
            {
                "data": serializer.data,
                "message": "Voice infra providers fetched successfully.",
            },
        )


class ProviderConfigurationsViewSet(viewsets.GenericViewSet):
    """
    API v2 Platform ViewSet for Provider Configurations
    """

    serializer_class = ProviderCredentialSerializer
    renderer_classes = [UnpodJSONRenderer]
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication, UnpodJSONWebTokenAuthentication]

    @extend_schema(
        tags=["Provider Configurations"],
        operation_id="Get Provider Configurations",
        parameters=[
            OpenApiParameter(
                name="Org-Handle",
                type=str,
                location=OpenApiParameter.HEADER,
                required=True,
                description="Organization domain handle",
            ),
        ],
        responses={
            200: OpenApiResponse(
                response=ProviderConfigurationsResponseSerializer,
                description="Fetch all Provider Configurations",
            ),
            401: UnAuthenticatedApiResponse,
        },
        description="Get all provider configurations for the organization.",
    )
    def get_provider_configurations(self, request, *args, **kwargs):
        """Get all provider configurations"""
        domain_handle = request.headers.get("Org-Handle", None)
        if not domain_handle:
            return Response(
                {
                    "status_code": 400,
                    "message": "Organization handle is required in Org-Handle header",
                },
                status=400,
            )

        from unpod.telephony.views import ProviderCredentialViewSet
        from unpod.space.models import SpaceOrganization

        viewset = ProviderCredentialViewSet(
            action="list", request=request, format_kwarg=None
        )
        viewset.args = args
        viewset.kwargs = kwargs
        response = viewset.list(request, *args, **kwargs)

        # Transform response to match API v2 format with exact field order
        if response.status_code == 200:
            configs = (
                response.data.get("data", response.data)
                if isinstance(response.data, dict)
                else response.data
            )
            if isinstance(configs, list):
                # Get org_handle lookup
                organization_ids = [config.get("organization") for config in configs if config.get("organization")]
                orgs = {
                    org.id: org.domain_handle
                    for org in SpaceOrganization.objects.filter(id__in=organization_ids)
                }

                transformed_configs = []
                for config in configs:
                    # Filter provider_details
                    provider = config.get("provider_details", {})
                    filtered_provider = (
                        {
                            "id": provider.get("id"),
                            "name": provider.get("name"),
                            "description": provider.get("description"),
                            "icon": provider.get("icon"),
                        }
                        if provider
                        else None
                    )

                    # Get org_handle from organization ID
                    organization_id = config.get("organization")
                    org_handle = orgs.get(organization_id) if organization_id else None

                    # Build new config with exact field order
                    transformed_config = {
                        "id": config.get("id"),
                        "name": config.get("name"),
                        "provider": config.get("provider"),
                        "provider_details": filtered_provider,
                        "org_handle": org_handle,
                        "meta_json": config.get("meta_json"),
                        "active": config.get("active"),
                        "api_key": config.get("api_key"),
                        "api_secret": config.get("api_secret"),
                        "base_url": config.get("base_url"),
                        "sip_url": config.get("sip_url"),
                    }
                    transformed_configs.append(transformed_config)

                # Update response data
                if isinstance(response.data, dict) and "data" in response.data:
                    response.data["data"] = transformed_configs
                else:
                    response.data = transformed_configs

        return response

    @extend_schema(
        tags=["Provider Configurations"],
        operation_id="Get Provider Configuration",
        parameters=[
            OpenApiParameter(
                name="Org-Handle",
                type=str,
                location=OpenApiParameter.HEADER,
                required=True,
                description="Organization domain handle",
            ),
        ],
        responses={
            200: OpenApiResponse(
                response=ProviderConfigurationResponseSerializer,
                description="Fetch single Provider Configuration",
                examples=[PROVIDER_CONFIG_RESPONSE_EXAMPLE],
            ),
            401: UnAuthenticatedApiResponse,
            404: OpenApiResponse(
                description="Configuration not found",
                response={
                    "type": "object",
                    "properties": {
                        "status_code": {"type": "integer"},
                        "message": {"type": "string"},
                    },
                },
            ),
        },
        description="Get a single provider configuration by ID.",
    )
    def get_configuration(self, request, *args, **kwargs):
        """Get single provider configuration by ID"""
        domain_handle = request.headers.get("Org-Handle", None)
        if not domain_handle:
            return Response(
                {
                    "status_code": 400,
                    "message": "Organization handle is required in Org-Handle header",
                },
                status=400,
            )

        from unpod.telephony.views import ProviderCredentialViewSet
        from unpod.space.models import SpaceOrganization

        viewset = ProviderCredentialViewSet(
            action="retrieve", request=request, format_kwarg=None
        )
        viewset.args = args
        viewset.kwargs = kwargs
        response = viewset.retrieve(request, *args, **kwargs)

        # Transform response to match API v2 format with exact field order
        if response.status_code == 200:
            config = (
                response.data.get("data", response.data)
                if isinstance(response.data, dict)
                else response.data
            )
            if isinstance(config, dict) and "id" in config:
                # Filter provider_details
                provider = config.get("provider_details", {})
                filtered_provider = (
                    {
                        "id": provider.get("id"),
                        "name": provider.get("name"),
                        "description": provider.get("description"),
                        "icon": provider.get("icon"),
                    }
                    if provider
                    else None
                )

                # Get org_handle from organization ID
                organization_id = config.get("organization")
                org_handle = None
                if organization_id:
                    org = SpaceOrganization.objects.filter(id=organization_id).first()
                    org_handle = org.domain_handle if org else None

                # Build new config with exact field order
                transformed_config = {
                    "id": config.get("id"),
                    "name": config.get("name"),
                    "provider": config.get("provider"),
                    "provider_details": filtered_provider,
                    "org_handle": org_handle,
                    "meta_json": config.get("meta_json"),
                    "active": config.get("active"),
                    "api_key": config.get("api_key"),
                    "api_secret": config.get("api_secret"),
                    "base_url": config.get("base_url"),
                    "sip_url": config.get("sip_url"),
                }

                # Update response data
                if isinstance(response.data, dict) and "data" in response.data:
                    response.data["data"] = transformed_config
                else:
                    response.data = transformed_config

        return response

    @extend_schema(
        tags=["Provider Configurations"],
        operation_id="Create Provider Configuration",
        parameters=[
            OpenApiParameter(
                name="Org-Handle",
                type=str,
                location=OpenApiParameter.HEADER,
                required=True,
                description="Organization domain handle",
            ),
        ],
        request=CreateProviderConfigurationSerializer,
        examples=[
            PROVIDER_CONFIG_VAPI_REQUEST_EXAMPLE,
            PROVIDER_CONFIG_LIVEKIT_REQUEST_EXAMPLE,
            PROVIDER_CONFIG_DAILY_REQUEST_EXAMPLE,
            PROVIDER_CONFIG_UNPOD_REQUEST_EXAMPLE,
            PROVIDER_CONFIG_WEBSOCKET_REQUEST_EXAMPLE,
        ],
        responses={
            200: OpenApiResponse(
                response=ProviderConfigurationResponseSerializer,
                description="Provider configuration created successfully",
                examples=[PROVIDER_CONFIG_RESPONSE_EXAMPLE],
            ),
            401: UnAuthenticatedApiResponse,
        },
        description="Create a new provider configuration.",
    )
    def create_configuration(self, request, *args, **kwargs):
        """Create provider configuration"""
        from unpod.telephony.views import ProviderCredentialViewSet
        from unpod.space.models import SpaceOrganization

        viewset = ProviderCredentialViewSet(
            action="create", request=request, format_kwarg=None
        )
        viewset.args = args
        viewset.kwargs = kwargs
        response = viewset.create(request, *args, **kwargs)

        # Transform response to match API v2 format with exact field order
        if response.status_code in [200, 201]:
            config = (
                response.data.get("data", response.data)
                if isinstance(response.data, dict)
                else response.data
            )
            if isinstance(config, dict) and "id" in config:
                # Filter provider_details
                provider = config.get("provider_details", {})
                filtered_provider = (
                    {
                        "id": provider.get("id"),
                        "name": provider.get("name"),
                        "description": provider.get("description"),
                        "icon": provider.get("icon"),
                    }
                    if provider
                    else None
                )

                # Get org_handle from organization ID
                organization_id = config.get("organization")
                org_handle = None
                if organization_id:
                    org = SpaceOrganization.objects.filter(id=organization_id).first()
                    org_handle = org.domain_handle if org else None

                # Build new config with exact field order
                transformed_config = {
                    "id": config.get("id"),
                    "name": config.get("name"),
                    "provider": config.get("provider"),
                    "provider_details": filtered_provider,
                    "org_handle": org_handle,
                    "meta_json": config.get("meta_json"),
                    "active": config.get("active"),
                    "api_key": config.get("api_key"),
                    "api_secret": config.get("api_secret"),
                    "base_url": config.get("base_url"),
                    "sip_url": config.get("sip_url"),
                }

                # Update response data
                if isinstance(response.data, dict) and "data" in response.data:
                    response.data["data"] = transformed_config
                else:
                    response.data = transformed_config

        return response

    @extend_schema(
        tags=["Provider Configurations"],
        operation_id="Update Provider Configuration",
        parameters=[
            OpenApiParameter(
                name="Org-Handle",
                type=str,
                location=OpenApiParameter.HEADER,
                required=True,
                description="Organization domain handle",
            ),
        ],
        request=UpdateProviderConfigurationSerializer,
        examples=[
            PROVIDER_CONFIG_UPDATE_VAPI_REQUEST_EXAMPLE,
            PROVIDER_CONFIG_UPDATE_LIVEKIT_REQUEST_EXAMPLE,
            PROVIDER_CONFIG_UPDATE_DAILY_REQUEST_EXAMPLE,
            PROVIDER_CONFIG_UPDATE_UNPOD_REQUEST_EXAMPLE,
            PROVIDER_CONFIG_UPDATE_WEBSOCKET_REQUEST_EXAMPLE,
        ],
        responses={
            200: OpenApiResponse(
                response=ProviderConfigurationResponseSerializer,
                description="Provider configuration updated successfully",
                examples=[PROVIDER_CONFIG_RESPONSE_EXAMPLE],
            ),
            401: UnAuthenticatedApiResponse,
        },
        description="Partial update a provider configuration by ID.",
    )
    def update_configuration(self, request, *args, **kwargs):
        """Partial update provider configuration"""
        from unpod.telephony.views import ProviderCredentialViewSet
        from unpod.space.models import SpaceOrganization

        viewset = ProviderCredentialViewSet(
            action="partial_update", request=request, format_kwarg=None
        )
        viewset.args = args
        viewset.kwargs = kwargs
        response = viewset.partial_update(request, *args, **kwargs)

        # Transform response to match API v2 format with exact field order
        if response.status_code == 200:
            config = (
                response.data.get("data", response.data)
                if isinstance(response.data, dict)
                else response.data
            )
            if isinstance(config, dict) and "id" in config:
                # Filter provider_details
                provider = config.get("provider_details", {})
                filtered_provider = (
                    {
                        "id": provider.get("id"),
                        "name": provider.get("name"),
                        "description": provider.get("description"),
                        "icon": provider.get("icon"),
                    }
                    if provider
                    else None
                )

                # Get org_handle from organization ID
                organization_id = config.get("organization")
                org_handle = None
                if organization_id:
                    org = SpaceOrganization.objects.filter(id=organization_id).first()
                    org_handle = org.domain_handle if org else None

                # Build new config with exact field order
                transformed_config = {
                    "id": config.get("id"),
                    "name": config.get("name"),
                    "provider": config.get("provider"),
                    "provider_details": filtered_provider,
                    "org_handle": org_handle,
                    "meta_json": config.get("meta_json"),
                    "active": config.get("active"),
                    "api_key": config.get("api_key"),
                    "api_secret": config.get("api_secret"),
                    "base_url": config.get("base_url"),
                    "sip_url": config.get("sip_url"),
                }

                # Update response data
                if isinstance(response.data, dict) and "data" in response.data:
                    response.data["data"] = transformed_config
                else:
                    response.data = transformed_config

        return response

    @extend_schema(
        tags=["Provider Configurations"],
        operation_id="Delete Provider Configuration",
        parameters=[
            OpenApiParameter(
                name="Org-Handle",
                type=str,
                location=OpenApiParameter.HEADER,
                required=True,
                description="Organization domain handle",
            ),
        ],
        responses={
            204: OpenApiResponse(
                description="Provider configuration deleted successfully",
                examples=[PROVIDER_CONFIG_DELETE_EXAMPLE],
            ),
            401: UnAuthenticatedApiResponse,
        },
        description="Delete a provider configuration by ID.",
    )
    def delete_configuration(self, request, *args, **kwargs):
        """Delete provider configuration"""
        from unpod.telephony.views import ProviderCredentialViewSet

        viewset = ProviderCredentialViewSet(
            action="destroy", request=request, format_kwarg=None
        )
        viewset.args = args
        viewset.kwargs = kwargs
        return viewset.destroy(request, *args, **kwargs)


class TelephonyBridgesViewSet(viewsets.GenericViewSet):
    """
    API v2 Platform ViewSet for Telephony Bridges
    """

    serializer_class = TaskRunSerializer
    renderer_classes = [UnpodJSONRenderer]
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication, UnpodJSONWebTokenAuthentication]

    # ============================================================================
    # Telephony APIs (API v2 Platform)
    # ============================================================================

    @extend_schema(
        tags=["Telephony - Bridges"],
        operation_id="List Telephony Bridges",
        parameters=[
            OpenApiParameter(
                name="Org-Handle",
                type=str,
                location=OpenApiParameter.HEADER,
                required=True,
                description="Organization domain handle",
            ),
            OpenApiParameter(
                name="Product-Id",
                type=str,
                location=OpenApiParameter.HEADER,
                required=True,
                default="unpod.dev",
                description="Product ID",
            ),
        ],
        responses={
            200: OpenApiResponse(
                response=VoiceBridgeListResponseSerializer,
                description="Successfully retrieved voice bridges",
                examples=[BRIDGES_LIST_EXAMPLE],
            ),
            206: OpenApiResponse(
                description="Business logic error",
                response={
                    "type": "object",
                    "properties": {"message": {"type": "string"}},
                },
            ),
        },
        description="Get all bridges for an organization",
    )
    def list_voice_bridges(self, request, *args, **kwargs):
        """List all voice bridges - direct model query, no loop"""
        from unpod.telephony.models import VoiceBridge
        from unpod.space.models import SpaceOrganization

        product_id = request.headers.get("Product-Id")
        domain_handle = request.headers.get("Org-Handle")

        if not product_id:
            return Response(
                {"message": "Please provide Product-Id in headers"}, status=206
            )

        if not domain_handle:
            return Response(
                {"message": "Please provide Org-Handle in headers"}, status=206
            )

        space_org = SpaceOrganization.objects.filter(
            domain_handle=domain_handle
        ).first()

        if not space_org:
            return Response({"message": "Organization not found"}, status=206)

        bridges = VoiceBridge.objects.filter(product_id=product_id, organization=space_org)

        paginator = UnpodCustomPagination(request, bridges, VoiceBridgeListSerializer)

        return paginator.get_paginated_response()

    @extend_schema(
        tags=["Telephony - Bridges"],
        operation_id="Get Voice Bridge",
        parameters=[
            OpenApiParameter(
                name="Org-Handle",
                type=str,
                location=OpenApiParameter.HEADER,
                required=True,
                description="Organization domain handle",
            ),
            OpenApiParameter(
                name="Product-Id",
                type=str,
                location=OpenApiParameter.HEADER,
                required=True,
                default="unpod.dev",
                description="Product ID",
            ),
        ],
        responses={
            200: OpenApiResponse(
                response=VoiceBridgeDetailResponseSerializer,
                description="Successfully retrieved voice bridge",
                examples=[BRIDGE_DETAIL_EXAMPLE],
            ),
            404: OpenApiResponse(
                description="Bridge not found",
                response={
                    "type": "object",
                    "properties": {
                        "status_code": {"type": "integer"},
                        "message": {"type": "string"},
                    },
                },
            ),
        },
        description="Get a single voice bridge by slug",
    )
    def get_voice_bridge(self, request, *args, **kwargs):
        """Get a single voice bridge by slug"""
        from unpod.telephony.views import VoiceBridgeViewSet
        from unpod.space.models import SpaceOrganization

        slug = kwargs.get("slug")
        viewset = VoiceBridgeViewSet(
            action="retrieve", request=request, format_kwarg=None
        )
        viewset.args = args
        viewset.kwargs = {"slug": slug}
        response = viewset.retrieve(request, slug=slug)

        # Transform response
        if response.status_code == 200:
            bridge = (
                response.data.get("data", response.data)
                if isinstance(response.data, dict)
                else response.data
            )
            if isinstance(bridge, dict) and "id" in bridge:
                # Get org_handle from organization ID
                organization_id = bridge.get("organization")
                org_handle = None
                if organization_id:
                    org = SpaceOrganization.objects.filter(id=organization_id).first()
                    org_handle = org.domain_handle if org else None

                # Transform numbers array - rename provider_credential and add org_handle
                numbers = bridge.get("numbers", [])
                transformed_numbers = []
                for num in numbers:
                    provider_cred = num.get("provider_credential", {})
                    transformed_provider_cred = None
                    if provider_cred:
                        # Get org_handle for provider_credential
                        cred_organization_id = provider_cred.get("organization")
                        cred_org_handle = None
                        if cred_organization_id:
                            cred_org = SpaceOrganization.objects.filter(
                                id=cred_organization_id
                            ).first()
                            cred_org_handle = (
                                cred_org.domain_handle if cred_org else None
                            )

                        # Filter provider_details
                        provider = provider_cred.get("provider_details", {})
                        filtered_provider = (
                            {
                                "id": provider.get("id"),
                                "name": provider.get("name"),
                                "description": provider.get("description"),
                                "icon": provider.get("icon"),
                            }
                            if provider
                            else None
                        )

                        transformed_provider_cred = {
                            "id": provider_cred.get("id"),
                            "name": provider_cred.get("name"),
                            "provider": provider_cred.get("provider"),
                            "provider_details": filtered_provider,
                            "org_handle": cred_org_handle,
                            "meta_json": provider_cred.get("meta_json"),
                            "api_key": provider_cred.get("api_key"),
                            "api_secret": provider_cred.get("api_secret"),
                            "base_url": provider_cred.get("base_url"),
                            "sip_url": provider_cred.get("sip_url"),
                        }

                    transformed_num = {
                        "id": num.get("id"),
                        "number_id": num.get("number_id"),
                        "number": num.get("number"),
                        "channels_count": num.get("channels_count"),
                        "provider_details": num.get("provider_details"),
                        "provider_configuration": transformed_provider_cred,
                        "agent_id": num.get("agent_id"),
                        "config_json": num.get("config_json"),
                    }
                    transformed_numbers.append(transformed_num)

                # Build transformed bridge response
                transformed_bridge = {
                    "id": bridge.get("id"),
                    "name": bridge.get("name"),
                    "description": bridge.get("description"),
                    "status": bridge.get("status"),
                    "documents_status": bridge.get("documents_status"),
                    "slug": bridge.get("slug"),
                    "numbers": transformed_numbers,
                    "org_handle": org_handle,
                    "region": bridge.get("region"),
                }

                # Update response data
                if isinstance(response.data, dict) and "data" in response.data:
                    response.data["data"] = transformed_bridge
                else:
                    response.data = transformed_bridge

        return response

    @extend_schema(
        tags=["Telephony - Bridges"],
        operation_id="Create Voice Bridge",
        parameters=[
            OpenApiParameter(
                name="Org-Handle",
                type=str,
                location=OpenApiParameter.HEADER,
                required=True,
                description="Organization domain handle",
            ),
            OpenApiParameter(
                name="Product-Id",
                type=str,
                location=OpenApiParameter.HEADER,
                required=True,
                default="unpod.dev",
                description="Product ID",
            ),
        ],
        request=VoiceBridgeSerializer,
        examples=[BRIDGE_CREATE_REQUEST_EXAMPLE],
        responses={
            201: OpenApiResponse(
                response=VoiceBridgeListResponseSerializer,
                description="Voice bridge created successfully",
                examples=[BRIDGE_CREATE_RESPONSE_EXAMPLE],
            ),
            400: {
                "type": "object",
                "properties": {
                    "status_code": {"type": "integer"},
                    "message": {"type": "string"},
                    "error": {"type": "string"},
                },
            },
        },
        description="Create a new voice bridge",
    )
    def create_voice_bridge(self, request, *args, **kwargs):
        """Create a new voice bridge"""
        from unpod.telephony.views import VoiceBridgeViewSet

        # Properly initialize viewset with all required attributes
        viewset = VoiceBridgeViewSet(
            action="create", request=request, format_kwarg=None
        )
        viewset.args = args
        viewset.kwargs = kwargs
        return viewset.create(request, *args, **kwargs)

    @extend_schema(
        tags=["Telephony - Bridges"],
        operation_id="Update Voice Bridge",
        request=VoiceBridgeSerializer,
        responses={
            200: OpenApiResponse(
                response=VoiceBridgeListResponseSerializer,
                description="Voice bridge updated successfully",
                examples=[BRIDGE_UPDATE_RESPONSE_EXAMPLE],
            ),
            206: {
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                    "data": {"type": "object"},
                },
            },
            400: {
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                    "data": {"type": "object"},
                },
            },
        },
        description="Update a voice bridge",
    )
    def update_voice_bridge(self, request, *args, **kwargs):
        """Update a voice bridge"""
        from unpod.telephony.views import VoiceBridgeViewSet

        slug = kwargs.get("slug")
        viewset = VoiceBridgeViewSet(
            action="update", request=request, format_kwarg=None
        )
        viewset.args = args
        viewset.kwargs = {"slug": slug}
        return viewset.update(request, slug=slug, partial=True)

    @extend_schema(
        tags=["Telephony - Bridges"],
        operation_id="Delete Voice Bridge",
        responses={
            204: OpenApiResponse(
                description="Bridge deleted successfully",
                examples=[BRIDGE_DELETE_EXAMPLE],
            ),
            206: {
                "type": "object",
                "properties": {"message": {"type": "string"}},
            },
            400: {
                "type": "object",
                "properties": {"message": {"type": "string"}},
            },
        },
        description="Delete a voice bridge",
    )
    def delete_voice_bridge(self, request, *args, **kwargs):
        """Delete a voice bridge"""
        from unpod.telephony.views import VoiceBridgeViewSet

        slug = kwargs.get("slug")
        viewset = VoiceBridgeViewSet(
            action="destroy", request=request, format_kwarg=None
        )
        viewset.request = request
        viewset.args = args
        viewset.kwargs = {"slug": slug}
        return viewset.destroy(request, slug=slug)

    @extend_schema(
        tags=["Telephony - Bridges"],
        operation_id="Connect Provider to Bridge",
        request=AssignNumberToBridgeSerializer,
        examples=[BRIDGE_CONNECT_PROVIDER_REQUEST_EXAMPLE],
        responses={
            201: {
                "type": "object",
                "properties": {
                    "data": {"type": "object"},
                    "message": {"type": "string"},
                    "number": {"type": "string"},
                },
            },
            206: {
                "type": "object",
                "properties": {"message": {"type": "string"}},
            },
            400: {
                "type": "object",
                "properties": {
                    "status_code": {"type": "integer"},
                    "message": {"type": "string"},
                    "error": {"type": "string"},
                },
            },
        },
        description="Connect a provider to a voice bridge. Provide the number_id and provider_credential_id in the request body.",
    )
    def connect_provider(self, request, *args, **kwargs):
        """Connect a provider to a bridge"""
        from unpod.telephony.views import VoiceBridgeViewSet

        slug = kwargs.get("slug")
        viewset = VoiceBridgeViewSet(
            action="numbers", request=request, format_kwarg=None
        )
        viewset.args = args
        viewset.kwargs = {"slug": slug}
        response = viewset.numbers(request, slug=slug)

        # Transform response - rename provider_credential to provider_configuration
        if response.status_code == 201 and "data" in response.data:
            data = response.data["data"]
            if "provider_credential" in data:
                data["provider_configuration"] = data.pop("provider_credential")
            # Remove number field (it's a queryset representation)
            data.pop("number", None)
            response.data.pop("number", None)

        return response

    @extend_schema(
        tags=["Telephony - Bridges"],
        operation_id="Disconnect Provider from Bridge",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "number_id": {"type": "integer"},
                },
                "required": ["number_id"],
            }
        },
        examples=[BRIDGE_DISCONNECT_PROVIDER_REQUEST_EXAMPLE],
        responses={
            200: {
                "type": "object",
                "properties": {
                    "status_code": {"type": "integer"},
                    "message": {"type": "string"},
                    "data": {"type": "object"},
                },
            },
            206: {
                "type": "object",
                "properties": {"message": {"type": "string"}},
            },
            400: {
                "type": "object",
                "properties": {
                    "status_code": {"type": "integer"},
                    "message": {"type": "string"},
                    "error": {"type": "string"},
                },
            },
        },
        description="Disconnect a provider from a voice bridge. Provide the number_id in the request body.",
    )
    def disconnect_provider(self, request, *args, **kwargs):
        """Disconnect a provider from a bridge"""
        from unpod.telephony.views import TelephonyNumberViewSet

        number_id = request.data.get("number_id")
        viewset = TelephonyNumberViewSet(
            action="unlink_provider", request=request, format_kwarg=None
        )
        viewset.args = args
        viewset.kwargs = {"pk": number_id}
        return viewset.unlink_provider(request, pk=number_id)


class CallLogsViewSet(viewsets.GenericViewSet):
    """
    API v2 Platform ViewSet for Call Logs
    """

    serializer_class = CallLogItemSerializer
    renderer_classes = [UnpodJSONRenderer]
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication, UnpodJSONWebTokenAuthentication]

    @extend_schema(
        tags=["Call Logs"],
        operation_id="Get Call Logs",
        parameters=[
            OpenApiParameter(
                name="Org-Handle",
                type=str,
                location=OpenApiParameter.HEADER,
                required=True,
                description="Organization domain handle. To get Org-Handle, use GET /api/v2/platform/organizations/ API.",
            ),
            OpenApiParameter(
                name="Product-Id",
                type=str,
                location=OpenApiParameter.HEADER,
                required=True,
                default="unpod.dev",
                description="Product ID for filtering call logs",
            ),
        ],
        responses={
            200: OpenApiResponse(
                response=CallLogsResponseSerializer,
                description="Successfully retrieved call logs",
                examples=[CALL_LOGS_LIST_EXAMPLE],
            ),
            400: {
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                    "error": {"type": "string"},
                },
            },
        },
        description="Get call history logs with filtering and pagination",
    )
    def get_call_logs(self, request, *args, **kwargs):
        domain_handle = request.headers.get("Org-Handle")
        product_id = request.headers.get("Product-Id")

        if not domain_handle:
            return Response(
                {"message": "Organization handle is required in Org-Handle header"},
                status=400,
            )

        if not product_id:
            return Response(
                {"message": "Product ID is required in Product-Id header"},
                status=400,
            )

        logs_data, success = fetch_call_logs(domain_handle, product_id, request)

        if success:
            return Response(
                {
                    "message": "Call logs fetched successfully",
                    "status_code": 200,
                    **logs_data,
                }
            )
        else:
            return Response(
                {
                    "message": "Failed to fetch call logs",
                    "error": logs_data.get("message", "Unknown error"),
                },
                status=400,
            )


class SpaceV2ViewSet(viewsets.GenericViewSet):
    """
    API v2 Platform ViewSet for Spaces
    - Returns lightweight space data for external users
    - No sensitive data like users, roles, permissions
    """

    renderer_classes = [UnpodJSONRenderer]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Spaces"],
        operation_id="List Spaces",
        parameters=[
            OpenApiParameter(
                name="Org-Handle",
                location=OpenApiParameter.HEADER,
                required=True,
                type=str,
                description="Organization domain handle",
            ),
        ],
        responses={
            200: OpenApiResponse(
                response=SpaceListResponseV2Serializer,
                description="List of spaces for the organization",
            ),
            401: UnAuthenticatedApiResponse,
        },
        description="Get all spaces for the authenticated user's organization.",
    )
    def list(self, request, *args, **kwargs):
        """List all spaces for the user's organization"""
        from unpod.space.models import Space, SpaceOrganization
        from unpod.apiV2Platform.serializers import SpaceListV2Serializer

        domain_handle = request.headers.get("Org-Handle", None)
        if not domain_handle:
            return Response(
                {"message": "Organization handle is required in Org-Handle header"},
                status=400,
            )

        # Get organization
        organization = SpaceOrganization.objects.filter(
            domain_handle=domain_handle
        ).first()
        if not organization:
            return Response(
                {"message": "Organization not found"},
                status=404,
            )

        # Get spaces for this organization
        queryset = (
            Space.objects.filter(
                space_organization=organization,
                status="active",
            )
            .select_related("space_organization")
            .order_by("-id")
        )

        serializer = SpaceListV2Serializer(queryset, many=True)

        return Response(
            {
                "message": "Spaces fetched successfully",
                "count": queryset.count(),
                "data": serializer.data,
            },
            status=200,
        )

    @extend_schema(
        tags=["Spaces"],
        operation_id="Get Space by Token",
        parameters=[
            OpenApiParameter(
                name="Org-Handle",
                location=OpenApiParameter.HEADER,
                required=True,
                type=str,
                description="Organization domain handle",
            ),
        ],
        responses={
            200: OpenApiResponse(
                response=SpaceDetailResponseV2Serializer,
                description="Space details",
            ),
            401: UnAuthenticatedApiResponse,
            404: OpenApiResponse(description="Space not found"),
        },
        description="Get a single space by its token.",
    )
    def retrieve(self, request, space_token, *args, **kwargs):
        """Get single space by token"""
        from unpod.space.models import Space
        from unpod.apiV2Platform.serializers import SpaceDetailV2Serializer

        domain_handle = request.headers.get("Org-Handle", None)
        if not domain_handle:
            return Response(
                {"message": "Organization handle is required in Org-Handle header"},
                status=400,
            )

        # Get space by token
        space = (
            Space.objects.filter(
                token=space_token,
                status="active",
                space_organization__domain_handle=domain_handle,
            )
            .select_related("space_organization")
            .first()
        )

        if not space:
            return Response(
                {"message": "Space not found"},
                status=404,
            )

        serializer = SpaceDetailV2Serializer(space)

        return Response(
            {
                "message": "Space fetched successfully",
                "data": serializer.data,
            },
            status=200,
        )

    @extend_schema(
        tags=["Spaces"],
        operation_id="List Organizations",
        responses={
            200: OpenApiResponse(
                description="List of organizations for the authenticated user",
                response={
                    "type": "object",
                    "properties": {
                        "message": {"type": "string"},
                        "count": {"type": "integer"},
                        "data": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "domain_handle": {"type": "string"},
                                    "token": {"type": "string"},
                                    "role": {"type": "string"},
                                    "domain": {"type": "string"},
                                    "is_private_domain": {"type": "boolean"},
                                },
                            },
                        },
                    },
                },
            ),
            401: UnAuthenticatedApiResponse,
        },
        description="Get all organizations that the authenticated user is a member of. Returns org-handles which can be used in Org-Handle header for other APIs.",
    )
    def list_organizations(self, request, *args, **kwargs):
        """List all organizations for the authenticated user"""
        from unpod.space.models import OrganizationMemberRoles

        org_list = []
        organization_list_obj = (
            OrganizationMemberRoles.objects.filter(
                user=request.user, organization__status="active"
            )
            .select_related("organization", "role")
            .values(
                "organization__name",
                "organization__token",
                "organization__domain",
                "organization__domain_handle",
                "organization__is_private_domain",
                "role__role_code",
            )
        )

        for org in organization_list_obj:
            org_list.append(
                {
                    "name": org["organization__name"],
                    "token": org["organization__token"],
                    "domain": org["organization__domain"],
                    "domain_handle": org["organization__domain_handle"],
                    "is_private_domain": org["organization__is_private_domain"],
                    "role": org["role__role_code"],
                }
            )

        return Response(
            {
                "message": "Organizations fetched successfully",
                "count": len(org_list),
                "data": org_list,
            },
            status=200,
        )
