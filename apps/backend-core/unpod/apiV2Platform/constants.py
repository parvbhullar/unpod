from drf_spectacular.utils import OpenApiResponse, OpenApiExample

CREATE_TASK_PAYLOAD = {
    "pilot": "space-agent-f1o3qjm1y7q1avvuynv4vprb1",
    "documents": [
        {
            "name": "Xyz",
            "time": "null",
            "email": "xyz@domain.com",
            "number": "1234567890",
            "context": "trial",
            "multi_select": "multi",
            "contact_number": "1234567890",
            "alternate_number": "9876543210",
            "created": "2025-10-30T05:44:56",
            "labels": ["Interested"],
            "title": "Document Title",
            "description": "Description text",
            "document_id": "6902fb5840a736e125e80ebc",
        }
    ],
    "context": "Call the lead and discuss the project requirements.",
    "schedule": {"type": "now"},
}


UnAuthenticatedApiResponse = OpenApiResponse(
    description="Unauthorized",
    response={
        "type": "object",
        "properties": {
            "status_code": {"type": "integer"},
            "message": {"type": "string"},
        },
    },
    examples=[
        OpenApiExample(
            name="Unauthorized Example",
            value={
                "status_code": 401,
                "message": "Authentication credentials were not provided.",
            },
        )
    ],
)

# Telephony Numbers Examples

TELEPHONY_NUMBER_EXAMPLE = OpenApiExample(
    name="Telephony Number",
    value={
        "status_code": 0,
        "message": "Telephony numbers fetched successfully.",
        "data": [{"id": 183, "number": "+1234567890", "active": True}],
    },
)

TELEPHONY_NUMBER_BAD_REQUEST_EXAMPLE = OpenApiExample(
    name="Bad Request Example",
    value={
        "status_code": 400,
        "message": "Organization handle is required in Org-Handle header.",
    },
)

# Telephony Providers Examples

PROVIDER_LIST_EXAMPLE = OpenApiExample(
    name="Provider List",
    value={
        "status_code": 200,
        "message": "Voice infra providers fetched successfully.",
        "data": [
            {
                "id": 1,
                "name": "Provider 1",
                "description": "Desc 1",
                "icon": "http://example.com/icon1.png",
            },
            {
                "id": 2,
                "name": "Provider 2",
                "description": "Desc 2",
                "icon": "http://example.com/icon2.png",
            },
        ],
    },
)

# Provider Configurations Examples

PROVIDER_CONFIG_RESPONSE_EXAMPLE = OpenApiExample(
    name="Provider Configuration Response",
    value={
        "status_code": 200,
        "message": "Success",
        "data": {
            "id": 1,
            "name": "Twilio Suport",
            "provider": 3,
            "provider_details": {
                "id": 3,
                "name": "Twilio",
                "description": "Desc 1",
                "icon": "https://ik.imagekit.io/techblog/channels/twilio.png",
            },
            "org_handle": "abc",
            "meta_json": [{"meta_key": "key", "meta_value": "mklsfjodfdo"}],
            "active": True,
            "api_key": "sk_xxx",
            "api_secret": "secret_xxx",
            "base_url": None,
            "sip_url": "",
        },
    },
    response_only=True,
)

PROVIDER_CONFIG_VAPI_REQUEST_EXAMPLE = OpenApiExample(
    "Vapi Configuration",
    value={
        "name": "My Vapi Configuration",
        "provider": 1,
        "api_key": "sk_xxx",
        "api_secret": "secret_xxx",
    },
    request_only=True,
)

PROVIDER_CONFIG_LIVEKIT_REQUEST_EXAMPLE = OpenApiExample(
    "Livekit Configuration",
    value={
        "name": "My Livekit Configuration",
        "provider": 2,
        "api_key": "sk_xxx",
        "api_secret": "secret_xxx",
        "base_url": "https://api.provider.com",
        "sip_url": "sip.provider.com",
    },
    request_only=True,
)

PROVIDER_CONFIG_DAILY_REQUEST_EXAMPLE = OpenApiExample(
    "Daily Configuration",
    value={
        "name": "My Daily Configuration",
        "provider": 3,
        "api_key": "sk_xxx",
        "api_secret": "secret_xxx",
    },
    request_only=True,
)

PROVIDER_CONFIG_UNPOD_REQUEST_EXAMPLE = OpenApiExample(
    "Unpod.ai Configuration",
    value={
        "name": "My Unpod.ai Configuration",
        "provider": 4,
        "api_key": "sk_xxx",
        "api_secret": "secret_xxx",
    },
    request_only=True,
)

PROVIDER_CONFIG_WEBSOCKET_REQUEST_EXAMPLE = OpenApiExample(
    "Websocket Configuration",
    value={
        "name": "My Websocket Configuration",
        "provider": 5,
        "api_key": "sk_xxx",
        "api_secret": "secret_xxx",
        "base_url": "https://api.provider.com",
    },
    request_only=True,
)

PROVIDER_CONFIG_DELETE_EXAMPLE = OpenApiExample(
    name="Delete Success",
    value={
        "status_code": 204,
        "message": "Provider configuration deleted successfully.",
    },
)

# Update Request Examples (without provider field)
PROVIDER_CONFIG_UPDATE_VAPI_REQUEST_EXAMPLE = OpenApiExample(
    "Vapi Configuration",
    value={
        "name": "My Vapi Configuration",
        "api_key": "sk_xxx",
        "api_secret": "secret_xxx",
    },
    request_only=True,
)

PROVIDER_CONFIG_UPDATE_LIVEKIT_REQUEST_EXAMPLE = OpenApiExample(
    "Livekit Configuration",
    value={
        "name": "My Livekit Configuration",
        "api_key": "sk_xxx",
        "api_secret": "secret_xxx",
        "base_url": "https://api.provider.com",
        "sip_url": "sip.provider.com",
    },
    request_only=True,
)

PROVIDER_CONFIG_UPDATE_DAILY_REQUEST_EXAMPLE = OpenApiExample(
    "Daily Configuration",
    value={
        "name": "My Daily Configuration",
        "api_key": "sk_xxx",
        "api_secret": "secret_xxx",
    },
    request_only=True,
)

PROVIDER_CONFIG_UPDATE_UNPOD_REQUEST_EXAMPLE = OpenApiExample(
    "Unpod.ai Configuration",
    value={
        "name": "My Unpod.ai Configuration",
        "api_key": "sk_xxx",
        "api_secret": "secret_xxx",
    },
    request_only=True,
)

PROVIDER_CONFIG_UPDATE_WEBSOCKET_REQUEST_EXAMPLE = OpenApiExample(
    "Websocket Configuration",
    value={
        "name": "My Websocket Configuration",
        "api_key": "sk_xxx",
        "api_secret": "secret_xxx",
        "base_url": "https://api.provider.com",
    },
    request_only=True,
)

# Telephony Bridges Examples

BRIDGES_LIST_EXAMPLE = OpenApiExample(
    name="Telephony Bridges List",
    value={
        "status_code": 200,
        "message": "Telephony bridges fetched successfully.",
        "data": [
            {
                "id": 1,
                "name": "My Bridge",
                "slug": "my-bridge-abc123",
                "status": "ACTIVE",
                "description": "Sample description",
            }
        ],
    },
    response_only=True,
)

BRIDGE_DETAIL_EXAMPLE = OpenApiExample(
    name="Voice Bridge Detail",
    value={
        "status_code": 200,
        "message": "Voice bridge fetched successfully.",
        "data": {
            "id": 1,
            "name": "My Bridge",
            "description": "",
            "status": "ACTIVE",
            "documents_status": "pending",
            "slug": "my-bridge-abc123",
            "numbers": [
                {
                    "id": 1,
                    "number_id": 1,
                    "number": "+1234567890",
                    "channels_count": 1,
                    "provider_details": None,
                    "provider_configuration": {
                        "id": 1,
                        "name": "My Config",
                        "provider": 1,
                        "provider_details": {
                            "id": 1,
                            "name": "Vapi",
                            "description": "Voice AI provider",
                            "icon": "https://example.com/icon.png",
                        },
                        "org_handle": "abc.co",
                        "meta_json": {},
                        "api_key": "sk_xxxx-xxxx-xxxx",
                        "api_secret": None,
                        "base_url": None,
                        "sip_url": None,
                    },
                    "agent_id": None,
                    "config_json": {},
                }
            ],
            "org_handle": "abc.co",
            "region": "India",
        },
    },
    response_only=True,
)

BRIDGE_CREATE_REQUEST_EXAMPLE = OpenApiExample(
    name="Create Voice Bridge Request",
    value={
        "name": "sanyam",
        "description": "",
        "status": "ACTIVE",
        "numberIds": [],
        "region": "IN",
    },
    request_only=True,
)

BRIDGE_CREATE_RESPONSE_EXAMPLE = OpenApiExample(
    name="Create Success",
    value={
        "status_code": 201,
        "message": "Voice bridge created successfully.",
        "data": {
            "id": 1,
            "name": "My Bridge",
            "description": "Sample description",
            "status": "ACTIVE",
            "documents_status": "pending",
            "slug": "my-bridge-abc123",
            "numbers": [
                {
                    "id": 1,
                    "number_id": 1,
                    "number": "+1234567890",
                    "channels_count": 1,
                    "provider_details": None,
                    "provider_configuration": {
                        "id": 1,
                        "name": "My Config",
                        "provider": 1,
                        "provider_details": {
                            "id": 1,
                            "name": "Provider Name",
                            "description": "Provider description",
                            "icon": "https://example.com/icon.png",
                        },
                        "org_handle": "abc",
                        "meta_json": {},
                        "api_key": "sk_xxx",
                        "api_secret": None,
                        "base_url": None,
                        "sip_url": None,
                    },
                    "agent_id": None,
                    "config_json": {},
                }
            ],
            "org_handle": "abc",
            "region": "India",
        },
    },
    response_only=True,
)

BRIDGE_UPDATE_RESPONSE_EXAMPLE = OpenApiExample(
    name="Update Success",
    value={
        "status_code": 200,
        "message": "Voice bridge updated successfully.",
        "data": {
            "id": 1,
            "name": "My Bridge",
            "description": "Sample description",
            "status": "ACTIVE",
            "documents_status": "pending",
            "slug": "my-bridge-abc123",
            "numbers": [
                {
                    "id": 1,
                    "number_id": 1,
                    "number": "+1234567890",
                    "channels_count": 1,
                    "provider_details": None,
                    "provider_configuration": {
                        "id": 1,
                        "name": "My Config",
                        "provider": 1,
                        "provider_details": {
                            "id": 1,
                            "name": "Provider Name",
                            "description": "Provider description",
                            "icon": "https://example.com/icon.png",
                        },
                        "org_handle": "abc",
                        "meta_json": {},
                        "api_key": "sk_xxx",
                        "api_secret": None,
                        "base_url": None,
                        "sip_url": None,
                    },
                    "agent_id": None,
                    "config_json": {},
                }
            ],
            "org_handle": "abc",
            "region": "India",
        },
    },
    response_only=True,
)

BRIDGE_DELETE_EXAMPLE = OpenApiExample(
    name="Delete Success",
    value={
        "status_code": 204,
        "message": "Bridge deleted successfully.",
    },
)

BRIDGE_CONNECT_PROVIDER_REQUEST_EXAMPLE = OpenApiExample(
    "Example Request",
    value={"number_id": 1, "provider_credential_id": 1},
    request_only=True,
    description="Connect a provider to a voice bridge with credentials",
)

BRIDGE_DISCONNECT_PROVIDER_REQUEST_EXAMPLE = OpenApiExample(
    "Example Request",
    value={"number_id": 183},
    request_only=True,
    description="Disconnect a provider from a voice bridge number",
)

# Call Logs Examples

CALL_LOGS_LIST_EXAMPLE = OpenApiExample(
    name="Call Logs List",
    value={
        "status_code": 200,
        "message": "Call logs fetched successfully",
        "count": 1,
        "data": [
            {
                "id": 39136,
                "call_status": "completed",
                "end_reason": "Customer Ended The Call",
                "call_type": "outbound",
                "bridge": 1,
                "agent": {"id": 573, "name": "Heeranandani thane"},
                "space": {"id": 346, "name": "Test Calls"},
                "creation_time": "2025-11-30T18:31:35Z",
                "start_time": "2025-11-30T18:30:24.041916Z",
                "end_time": "2025-11-30T18:31:20.669045Z",
                "call_duration": 56.627129,
                "source_number": "+919876543210",
                "destination_number": "911234567890",
            }
        ],
    },
)
