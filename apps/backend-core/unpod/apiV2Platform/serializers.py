from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample

from unpod.apiV2Platform.constants import CREATE_TASK_PAYLOAD
from unpod.core_components.models import TelephonyNumber
from unpod.core_components.serializers import ProviderSerializer
from unpod.core_components.tasks.serializers import TaskRunSerializer
from unpod.metrics.serializers import CallLogSerializer
from unpod.telephony.serializers import ProviderCredentialSerializer
from unpod.space.models import Space
from unpod.common.storage_backends import imagekitBackend


@extend_schema_serializer(
    examples=[OpenApiExample("Create Task Run Request", value=CREATE_TASK_PAYLOAD)]
)
class SpaceTaskRunSerializer(TaskRunSerializer):
    """Serializer for creating task runs in a space"""

    pass


class TelephonyNumberSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelephonyNumber
        fields = ["id", "number", "active"]


class TelephonyNumberResponseSerializer(serializers.Serializer):
    """Response schema for telephony number listing"""

    status_code = serializers.IntegerField()
    message = serializers.CharField()
    data = TelephonyNumberSerializer(many=True)


class TelephonyProviderSerializer(ProviderSerializer):
    """
    Serializer for telephony provider information
    """

    class Meta(ProviderSerializer.Meta):
        fields = ["id", "name", "description", "icon"]


# ============================================================================
# Voice Bridge Serializers (for apiV2Platform - filtered response)
# ============================================================================


class BridgeProviderDetailsSerializer(serializers.Serializer):
    """Minimal provider details for bridge numbers"""

    id = serializers.IntegerField()
    name = serializers.CharField()


class BridgeNumberSerializer(serializers.Serializer):
    """Filtered bridge number - only essential fields"""

    provider_details = BridgeProviderDetailsSerializer()
    state = serializers.CharField()
    active = serializers.BooleanField()
    status = serializers.CharField()


class VoiceBridgeListSerializer(serializers.Serializer):
    """Voice bridge with filtered numbers"""

    id = serializers.IntegerField()
    name = serializers.CharField()
    slug = serializers.CharField()
    status = serializers.CharField()
    description = serializers.CharField(allow_null=True)


class VoiceBridgeListResponseSerializer(serializers.Serializer):
    """Response schema for voice bridge listing"""

    count = serializers.IntegerField()
    status_code = serializers.IntegerField()
    message = serializers.CharField()
    data = VoiceBridgeListSerializer(many=True)


class VoiceBridgeDetailResponseSerializer(serializers.Serializer):
    """Response schema for single voice bridge"""

    status_code = serializers.IntegerField()
    message = serializers.CharField()
    data = VoiceBridgeListSerializer()


class ProviderResponseSerializer(serializers.Serializer):
    """Response schema for provider listing"""

    status_code = serializers.IntegerField()
    message = serializers.CharField()
    data = TelephonyProviderSerializer(many=True)


class ProviderConfigurationsSerializer(ProviderCredentialSerializer):
    provider_details = TelephonyProviderSerializer(source="provider", read_only=True)

    class Meta(ProviderCredentialSerializer.Meta):
        fields = [
            "id",
            "name",
            "provider",
            "meta_json",
            "active",
            "api_key",
            "api_secret",
            "base_url",
            "sip_url",
            "is_valid",
            "provider_details",
        ]


class CreateProviderConfigurationSerializer(serializers.Serializer):
    """Request serializer for creating provider configuration"""

    name = serializers.CharField(required=True, help_text="Configuration name")
    provider = serializers.IntegerField(required=True, help_text="Provider ID")
    api_key = serializers.CharField(required=False, help_text="API key")
    api_secret = serializers.CharField(required=False, help_text="API secret")
    base_url = serializers.CharField(required=False, help_text="Base URL")
    sip_url = serializers.CharField(required=False, help_text="SIP URL")


class UpdateProviderConfigurationSerializer(serializers.Serializer):
    """Request serializer for updating provider configuration"""

    name = serializers.CharField(required=False, help_text="Updated configuration name")
    api_key = serializers.CharField(required=False, help_text="Updated API key")
    api_secret = serializers.CharField(required=False, help_text="Updated API secret")
    base_url = serializers.CharField(required=False, help_text="Updated Base URL")
    sip_url = serializers.CharField(required=False, help_text="Updated SIP URL")


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Provider Configurations List",
            value={
                "status_code": 200,
                "message": "Success",
                "data": [
                    {
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
                        "api_key": "dsds15415xxxxxs54fs5",
                        "api_secret": "sfs1f5xxxxx4fs4f",
                        "base_url": None,
                        "sip_url": "",
                    }
                ],
            },
            response_only=True,
        )
    ]
)
class ProviderConfigurationsResponseSerializer(serializers.Serializer):
    """Response schema for provider credential"""

    status_code = serializers.IntegerField()
    message = serializers.CharField()
    data = ProviderConfigurationsSerializer(many=True)


class ProviderConfigurationResponseSerializer(serializers.Serializer):
    """Response schema for provider credential"""

    status_code = serializers.IntegerField()
    message = serializers.CharField()
    data = ProviderConfigurationsSerializer()


class AssignNumberToBridgeSerializer(serializers.Serializer):
    """Simplified serializer for assigning a number to a bridge"""

    number_id = serializers.IntegerField(
        required=True, help_text="Telephony number ID (e.g., 183)"
    )
    provider_credential_id = serializers.IntegerField(
        required=True, help_text="Provider credential ID (e.g., 1)"
    )


class TaskRunDataSerializer(serializers.Serializer):
    """Data object in task run creation response"""

    run_id = serializers.CharField()
    space_id = serializers.CharField()
    status = serializers.CharField()
    created = serializers.DateTimeField()
    _id = serializers.CharField()


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Task Created Successfully",
            value={
                "status_code": 200,
                "message": "Task Created Successfully",
                "data": {
                    "run_id": "Rf36292fceaa211ef8e2a91681c5ad3ab",
                    "space_id": "321",
                    "status": "pending",
                    "created": "2025-11-17T10:30:00.000000",
                    "_id": "67aeecb2851179ff81e48f64",
                },
            },
            response_only=True,
        )
    ]
)
class TaskRunCreateResponseSerializer(serializers.Serializer):
    """Response schema for POST /api/v2/platform/tasks/{space_token}/"""

    status_code = serializers.IntegerField()
    message = serializers.CharField()
    data = TaskRunDataSerializer()


class UserInfoSerializer(serializers.Serializer):
    id = serializers.CharField()
    email = serializers.EmailField()
    full_name = serializers.CharField()
    user_token = serializers.CharField()


class RunItemSerializer(serializers.Serializer):
    _id = serializers.CharField()
    space_id = serializers.CharField()
    thread_id = serializers.CharField(allow_null=True)
    user = serializers.CharField()
    user_org_id = serializers.CharField(allow_null=True)
    user_info = UserInfoSerializer()
    created = serializers.DateTimeField()
    modified = serializers.DateTimeField()
    run_id = serializers.CharField()
    batch_count = serializers.IntegerField()
    collection_ref = serializers.CharField()
    status = serializers.CharField()
    run_mode = serializers.CharField()


class RunListResponseData(serializers.Serializer):
    data = RunItemSerializer(many=True)
    count = serializers.IntegerField()
    status_code = serializers.IntegerField()
    message = serializers.CharField()


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Runs Response",
            value={
                "count": 1,
                "status_code": 200,
                "message": "Runs Fetched Successfully",
                "data": [
                    {
                        "_id": "abc123def456ghi789jkl0",
                        "space_id": "space987654321",
                        "thread_id": "thread123456789",
                        "user": "user001",
                        "user_org_id": "org56789",
                        "user_info": {
                            "id": "user001",
                            "email": "user@example.com",
                            "full_name": "John Smith",
                            "user_token": "token9876543210abcdef",
                        },
                        "created": "2025-11-18T11:13:58.671Z",
                        "modified": "2025-11-18T11:13:58.671Z",
                        "run_id": "run1234567890abcdef",
                        "batch_count": 1,
                        "collection_ref": "collection_abc123xyz789",
                        "status": "completed",
                        "run_mode": "automatic",
                    }
                ],
            },
            response_only=True,
        )
    ]
)
class RunListResponseSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    status_code = serializers.IntegerField()
    message = serializers.CharField()
    data = RunItemSerializer(many=True)


class CustomerSerializer(serializers.Serializer):
    """Customer information in output"""

    number = serializers.CharField(required=False)
    name = serializers.CharField(required=False)


class MessageSerializer(serializers.Serializer):
    """Individual message in transcript"""

    role = serializers.CharField(required=False)
    time = serializers.FloatField(required=False)
    endTime = serializers.FloatField(required=False)
    message = serializers.CharField(required=False)
    duration = serializers.FloatField(required=False)
    secondsFromStart = serializers.FloatField(required=False)
    source = serializers.CharField(required=False, allow_blank=True)


class AnalysisCostBreakdownSerializer(serializers.Serializer):
    """Analysis cost breakdown"""

    summary = serializers.FloatField(required=False)
    structuredData = serializers.FloatField(required=False)
    successEvaluation = serializers.FloatField(required=False)
    summaryPromptTokens = serializers.IntegerField(required=False)
    summaryCompletionTokens = serializers.IntegerField(required=False)
    structuredDataPromptTokens = serializers.IntegerField(required=False)
    successEvaluationPromptTokens = serializers.IntegerField(required=False)
    structuredDataCompletionTokens = serializers.IntegerField(required=False)
    successEvaluationCompletionTokens = serializers.IntegerField(required=False)


class CostBreakdownSerializer(serializers.Serializer):
    """Cost breakdown for the call"""

    stt = serializers.FloatField(required=False)
    llm = serializers.FloatField(required=False)
    tts = serializers.FloatField(required=False)
    vapi = serializers.FloatField(required=False)
    total = serializers.FloatField(required=False)
    llmPromptTokens = serializers.IntegerField(required=False)
    llmCompletionTokens = serializers.IntegerField(required=False)
    ttsCharacters = serializers.IntegerField(required=False)
    analysisCostBreakdown = AnalysisCostBreakdownSerializer(required=False)


class AnalysisSerializer(serializers.Serializer):
    """Analysis results"""

    summary = serializers.CharField(required=False)
    successEvaluation = serializers.CharField(required=False)


class ArtifactMessageSerializer(serializers.Serializer):
    """Messages in artifact"""

    role = serializers.CharField(required=False)
    time = serializers.FloatField(required=False)
    message = serializers.CharField(required=False)


class OpenAIMessageSerializer(serializers.Serializer):
    """OpenAI formatted messages"""

    content = serializers.CharField(required=False)
    role = serializers.CharField(required=False)


class ArtifactSerializer(serializers.Serializer):
    """Artifact with recordings and messages"""

    recordingUrl = serializers.URLField(required=False)
    stereoRecordingUrl = serializers.URLField(required=False)
    messages = ArtifactMessageSerializer(many=True, required=False)
    messagesOpenAIFormatted = OpenAIMessageSerializer(many=True, required=False)
    transcript = serializers.CharField(required=False)


class TranscriberSerializer(serializers.Serializer):
    """Transcriber configuration"""

    model = serializers.CharField(required=False)
    provider = serializers.CharField(required=False)


class ModelSerializer(serializers.Serializer):
    """LLM model configuration"""

    model = serializers.CharField(required=False)
    provider = serializers.CharField(required=False)


class VoiceSerializer(serializers.Serializer):
    """Voice configuration"""

    model = serializers.CharField(required=False)
    voiceId = serializers.CharField(required=False)
    provider = serializers.CharField(required=False)


class CostItemSerializer(serializers.Serializer):
    """Individual cost item"""

    cost = serializers.FloatField(required=False)
    type = serializers.CharField(required=False)
    minutes = serializers.FloatField(required=False)
    transcriber = TranscriberSerializer(required=False)
    model = ModelSerializer(required=False)
    voice = VoiceSerializer(required=False)
    characters = serializers.IntegerField(required=False)
    promptTokens = serializers.IntegerField(required=False)
    completionTokens = serializers.IntegerField(required=False)
    subType = serializers.CharField(required=False)
    analysisType = serializers.CharField(required=False)


class MonitorSerializer(serializers.Serializer):
    """Monitor URLs"""

    listenUrl = serializers.URLField(required=False)
    controlUrl = serializers.URLField(required=False)


class OutputSerializer(serializers.Serializer):
    """Complete output object from task execution"""

    id = serializers.CharField(required=False)
    assistantId = serializers.CharField(required=False)
    phoneNumberId = serializers.CharField(required=False)
    type = serializers.CharField(required=False)
    startedAt = serializers.DateTimeField(required=False)
    endedAt = serializers.DateTimeField(required=False)
    transcript = serializers.CharField(required=False)
    recordingUrl = serializers.URLField(required=False)
    summary = serializers.CharField(required=False)
    createdAt = serializers.DateTimeField(required=False)
    updatedAt = serializers.DateTimeField(required=False)
    orgId = serializers.CharField(required=False)
    cost = serializers.FloatField(required=False)
    customer = CustomerSerializer(required=False)
    status = serializers.CharField(required=False)
    endedReason = serializers.CharField(required=False)
    messages = MessageSerializer(many=True, required=False)
    stereoRecordingUrl = serializers.URLField(required=False)
    costBreakdown = CostBreakdownSerializer(required=False)
    phoneCallProvider = serializers.CharField(required=False)
    phoneCallProviderId = serializers.CharField(required=False)
    phoneCallTransport = serializers.CharField(required=False)
    analysis = AnalysisSerializer(required=False)
    artifact = ArtifactSerializer(required=False)
    costs = CostItemSerializer(many=True, required=False)
    monitor = MonitorSerializer(required=False)
    transport = serializers.DictField(required=False)


class InputSerializer(serializers.Serializer):
    """Input data for the task"""

    contact_name = serializers.CharField(required=False)
    contact_number = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    address = serializers.CharField(required=False)
    occupation = serializers.CharField(required=False)
    content_hash = serializers.CharField(required=False)
    file_sha1 = serializers.CharField(required=False)
    id = serializers.CharField(required=False)
    # Additional fields for agent tasks
    name = serializers.CharField(required=False)
    about = serializers.CharField(required=False)
    company_name = serializers.CharField(required=False)
    created = serializers.DateTimeField(required=False)
    context = serializers.CharField(required=False)


class TaskObjectSerializer(serializers.Serializer):
    """Task objective"""

    objective = serializers.CharField(required=False)


class TaskDetailSerializer(serializers.Serializer):
    """
    Detailed task object with complete schema
    Used for: GET /api/v2/platform/runs/<space_token>/<run_id>/
    """

    _id = serializers.CharField()
    space_id = serializers.CharField()
    thread_id = serializers.CharField(allow_null=True, required=False)
    user = serializers.CharField()
    user_org_id = serializers.CharField(allow_null=True, required=False)
    user_info = UserInfoSerializer(required=False)
    created = serializers.DateTimeField()
    modified = serializers.DateTimeField(required=False)
    task_id = serializers.CharField()
    run_id = serializers.CharField()
    collection_ref = serializers.CharField(required=False)
    task = TaskObjectSerializer(required=False)
    input = InputSerializer(required=False)
    output = OutputSerializer(required=False)
    attachments = serializers.ListField(required=False)
    assignee = serializers.CharField(required=False)
    status = serializers.CharField()
    execution_type = serializers.CharField(required=False)
    ref_id = serializers.CharField(required=False)


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Task Detail Response",
            value={
                "count": 1,
                "status_code": 200,
                "message": "Tasks Fetched Successfully",
                "data": [
                    {
                        "_id": "67abc123def456789",
                        "space_id": "space-uuid-123",
                        "thread_id": None,
                        "user": "user-123",
                        "user_org_id": None,
                        "user_info": {
                            "id": "user-123",
                            "email": "user@example.com",
                            "full_name": "John Doe",
                            "user_token": "ABCD1234EFGH5678",
                        },
                        "created": "2025-11-17T12:00:00.000Z",
                        "modified": "2025-11-17T12:30:00.000Z",
                        "task_id": "task-uuid-456",
                        "run_id": "run-uuid-789",
                        "collection_ref": "collection_data_XYZ123",
                        "task": {"objective": "Call customer and confirm appointment"},
                        "input": {
                            "contact_name": "Alice Smith",
                            "contact_number": "+1234567890",
                            "email": "alice@example.com",
                            "address": "123 Main St, City",
                            "occupation": "Software Engineer",
                            "content_hash": "abc123hash",
                            "file_sha1": "def456sha",
                            "id": "doc-123",
                        },
                        "output": {
                            "id": "call-uuid-001",
                            "assistantId": "assistant-123",
                            "phoneNumberId": "phone-456",
                            "type": "outbound",
                            "startedAt": "2025-11-17T12:05:00.000Z",
                            "endedAt": "2025-11-17T12:10:00.000Z",
                            "transcript": "Agent: Hello, this is calling to confirm...\nCustomer: Yes, confirmed.",
                            "recordingUrl": "https://example.com/recordings/rec123.mp3",
                            "summary": "Customer confirmed the appointment for tomorrow at 2 PM",
                            "createdAt": "2025-11-17T12:05:00.000Z",
                            "updatedAt": "2025-11-17T12:10:00.000Z",
                            "orgId": "org-789",
                            "cost": 0.45,
                            "customer": {
                                "number": "+1234567890",
                                "name": "Alice Smith",
                            },
                            "status": "completed",
                            "endedReason": "customer-ended-call",
                            "messages": [
                                {
                                    "role": "agent",
                                    "time": 1.5,
                                    "endTime": 5.2,
                                    "message": "Hello, this is calling to confirm your appointment",
                                    "duration": 3.7,
                                    "secondsFromStart": 1.5,
                                },
                                {
                                    "role": "customer",
                                    "time": 5.5,
                                    "endTime": 8.0,
                                    "message": "Yes, I confirm",
                                    "duration": 2.5,
                                    "secondsFromStart": 5.5,
                                },
                            ],
                            "stereoRecordingUrl": "https://example.com/recordings/rec123-stereo.mp3",
                            "costBreakdown": {
                                "stt": 0.05,
                                "llm": 0.25,
                                "tts": 0.10,
                                "vapi": 0.05,
                                "total": 0.45,
                                "llmPromptTokens": 150,
                                "llmCompletionTokens": 80,
                                "ttsCharacters": 200,
                                "analysisCostBreakdown": {
                                    "summary": 0.02,
                                    "structuredData": 0.03,
                                    "successEvaluation": 0.02,
                                    "summaryPromptTokens": 50,
                                    "summaryCompletionTokens": 30,
                                    "structuredDataPromptTokens": 60,
                                    "successEvaluationPromptTokens": 40,
                                    "structuredDataCompletionTokens": 35,
                                    "successEvaluationCompletionTokens": 25,
                                },
                            },
                            "phoneCallProvider": "twilio",
                            "phoneCallProviderId": "twilio-call-123",
                            "phoneCallTransport": "sip",
                            "analysis": {
                                "summary": "Customer confirmed appointment successfully",
                                "successEvaluation": "success",
                            },
                            "artifact": {
                                "recordingUrl": "https://example.com/recordings/rec123.mp3",
                                "stereoRecordingUrl": "https://example.com/recordings/rec123-stereo.mp3",
                                "messages": [
                                    {
                                        "role": "agent",
                                        "time": 1.5,
                                        "message": "Hello, this is calling to confirm your appointment",
                                    }
                                ],
                                "messagesOpenAIFormatted": [
                                    {
                                        "content": "Hello, this is calling to confirm your appointment",
                                        "role": "assistant",
                                    }
                                ],
                                "transcript": "Full transcript here...",
                            },
                            "costs": [
                                {
                                    "cost": 0.25,
                                    "type": "llm",
                                    "minutes": 0,
                                    "model": {"model": "gpt-4", "provider": "openai"},
                                    "promptTokens": 150,
                                    "completionTokens": 80,
                                },
                                {
                                    "cost": 0.10,
                                    "type": "tts",
                                    "minutes": 0,
                                    "voice": {
                                        "model": "eleven_turbo_v2",
                                        "voiceId": "voice-123",
                                        "provider": "elevenlabs",
                                    },
                                    "characters": 200,
                                },
                            ],
                            "monitor": {
                                "listenUrl": "https://example.com/monitor/listen/123",
                                "controlUrl": "https://example.com/monitor/control/123",
                            },
                            "transport": {},
                        },
                        "attachments": [],
                        "assignee": "agent-handle-123",
                        "status": "completed",
                        "execution_type": "call",
                        "ref_id": "doc-123",
                    }
                ],
            },
            response_only=True,
        )
    ]
)
class TaskDetailResponseSerializer(serializers.Serializer):
    """
    Response schema for GET /api/v2/platform/runs/<space_token>/<run_id>/
    Returns detailed task list with metadata
    """

    count = serializers.IntegerField()
    status_code = serializers.IntegerField(required=False)
    message = serializers.CharField()
    data = TaskDetailSerializer(many=True)


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Agent Tasks Response",
            value={
                "count": 1,
                "status_code": 200,
                "message": "Tasks Fetched Successfully",
                "data": [
                    {
                        "_id": "example123456789",
                        "space_id": "999",
                        "thread_id": None,
                        "user": "101",
                        "user_org_id": "501",
                        "user_info": {
                            "id": "101",
                            "email": "demo.user@example.com",
                            "full_name": "Demo User",
                            "user_token": "DEMO123TOKEN456",
                        },
                        "created": "2025-01-10T10:20:30.000000",
                        "modified": "2025-01-10T10:25:30.000000",
                        "task_id": "TASK123456789",
                        "run_id": "RUN123456789",
                        "collection_ref": "collection_data_DEMO123456",
                        "task": {"objective": "call"},
                        "input": {
                            "name": "John Doe",
                            "about": "Software Developer",
                            "email": "john.doe@example.com",
                            "address": "New Delhi",
                            "occupation": "Developer",
                            "company_name": "TechCorp",
                            "contact_number": "9876543210",
                            "created": "2025-01-01T12:00:00.000000",
                            "context": "Policy Number 123456789, Amount Rupees ten thousand, Due Date 10th March 2025",
                        },
                        "output": {},
                        "attachments": [],
                        "assignee": "sales-agent-v1",
                        "status": "pending",
                        "execution_type": "call",
                        "ref_id": "doc-123456",
                    }
                ],
            },
            response_only=True,
        )
    ]
)
class AgentTasksResponseSerializer(serializers.Serializer):
    """
    Response schema for GET /api/v2/platform/tasks/agents/{agent_id}/
    Returns tasks assigned to a specific agent
    """

    count = serializers.IntegerField()
    status_code = serializers.IntegerField(required=False)
    message = serializers.CharField()
    data = TaskDetailSerializer(many=True)


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Space Tasks Response",
            value={
                "count": 1,
                "status_code": 200,
                "message": "Tasks Fetched Successfully",
                "data": [
                    {
                        "_id": "space_task_id_001",
                        "space_id": "999",
                        "thread_id": None,
                        "user": "456",
                        "user_org_id": "789",
                        "user_info": {
                            "id": "456",
                            "email": "sales.manager@company.com",
                            "full_name": "Sarah Johnson",
                            "user_token": "SPACE_TOKEN_ABC123",
                        },
                        "created": "2025-01-15T14:30:00.000000",
                        "modified": "2025-01-15T14:35:00.000000",
                        "task_id": "TASK_SPACE_456789",
                        "run_id": "RUN_SPACE_987654",
                        "collection_ref": "collection_data_SPACE123456",
                        "task": {
                            "objective": "Follow up with potential clients for product demo"
                        },
                        "input": {
                            "name": "Rajesh Kumar",
                            "contact_number": "+919988776655",
                            "email": "rajesh.kumar@techstart.in",
                            "address": "Bangalore, Karnataka, India",
                            "occupation": "CTO",
                            "company_name": "TechStart Solutions",
                            "context": "Interested in AI automation tools for their startup. Budget: 50K-1L, Timeline: Q1 2025",
                        },
                        "output": {
                            "id": "call_space_output_001",
                            "assistantId": "assistant_sales_v3",
                            "phoneNumberId": "phone_india_001",
                            "type": "outboundPhoneCall",
                            "startedAt": "2025-01-15T14:30:15.000Z",
                            "endedAt": "2025-01-15T14:38:45.000Z",
                            "transcript": "Agent: Hello, may I speak with Mr. Rajesh Kumar?\nCustomer: Yes, speaking.\nAgent: Hi Rajesh, this is calling from AI Solutions. We discussed our automation platform last week. Do you have a few minutes?\nCustomer: Yes, I remember. Go ahead.\nAgent: Great! I wanted to schedule a product demo for your team. Would next Tuesday work?\nCustomer: Tuesday works. What time?\nAgent: How about 3 PM IST?\nCustomer: Perfect. Please send a calendar invite.\nAgent: Absolutely. I'll send it right away with the demo link.\nCustomer: Thanks!\nAgent: You're welcome. Looking forward to showing you our platform. Have a great day!\nCustomer: You too, bye.",
                            "recordingUrl": "https://storage.example.com/recordings/space_call_001.mp3",
                            "summary": "Successfully scheduled product demo with Rajesh Kumar (CTO, TechStart Solutions) for next Tuesday at 3 PM IST. Client is interested in AI automation tools with budget range 50K-1L for Q1 2025 deployment.",
                            "createdAt": "2025-01-15T14:30:10.000Z",
                            "updatedAt": "2025-01-15T14:39:00.000Z",
                            "orgId": "org-space-12345",
                            "cost": 0.18,
                            "customer": {
                                "number": "+919988776655",
                                "name": "Rajesh Kumar",
                            },
                            "status": "completed",
                            "endedReason": "assistant-ended-call",
                        },
                        "attachments": [],
                        "assignee": "sales-bot-v3",
                        "status": "completed",
                        "execution_type": "call",
                        "ref_id": "lead_doc_456789",
                    },
                    {
                        "_id": "space_task_id_002",
                        "space_id": "999",
                        "thread_id": None,
                        "user": "456",
                        "user_org_id": "789",
                        "user_info": {
                            "id": "456",
                            "email": "sales.manager@company.com",
                            "full_name": "Sarah Johnson",
                            "user_token": "SPACE_TOKEN_ABC123",
                        },
                        "created": "2025-01-15T13:20:00.000000",
                        "modified": "2025-01-15T13:20:00.000000",
                        "task_id": "TASK_SPACE_456790",
                        "run_id": "RUN_SPACE_987655",
                        "collection_ref": "collection_data_SPACE123456",
                        "task": {
                            "objective": "Payment reminder for invoice #INV-2025-001"
                        },
                        "input": {
                            "name": "Priya Sharma",
                            "contact_number": "+919876543210",
                            "email": "priya.sharma@business.com",
                            "address": "Mumbai, Maharashtra",
                            "occupation": "Finance Manager",
                            "company_name": "Global Enterprises Ltd",
                            "context": "Pending invoice INV-2025-001 amount Rs. 45,000, due date: 20th Jan 2025",
                        },
                        "output": {},
                        "attachments": [],
                        "assignee": "payment-bot-v1",
                        "status": "pending",
                        "execution_type": "call",
                        "ref_id": "invoice_doc_001",
                    },
                ],
            },
            response_only=True,
        )
    ]
)
class SpaceTasksResponseSerializer(serializers.Serializer):
    """
    Response schema for GET /api/v2/platform/tasks/spaces/{space_token}/
    Returns all tasks for a specific space with pagination
    """

    count = serializers.IntegerField()
    status_code = serializers.IntegerField(required=False)
    message = serializers.CharField()
    data = TaskDetailSerializer(many=True)


class CallLogItemSerializer(CallLogSerializer):
    """Individual call log item"""

    pass

    # id = serializers.CharField()
    # source_number = serializers.CharField()
    # destination_number = serializers.CharField()
    # call_type = serializers.CharField()
    # call_status = serializers.CharField()
    # creation_time = serializers.DateTimeField()
    # start_time = serializers.DateTimeField(required=False, allow_null=True)
    # end_time = serializers.DateTimeField(required=False, allow_null=True)
    # call_duration = serializers.DurationField(required=False, allow_null=True)
    # end_reason = serializers.CharField(required=False, allow_null=True)
    # bridge = serializers.IntegerField(required=False, allow_null=True)


class CallLogsResponseSerializer(serializers.Serializer):
    """
    Response schema for GET /api/v2/platform/call-logs/
    Returns call history logs with filtering and pagination
    """

    status_code = serializers.IntegerField(required=False)
    message = serializers.CharField()
    count = serializers.IntegerField()
    data = CallLogItemSerializer(many=True)


# ============================================================================
# Space V2 Serializers (for apiV2Platform - lightweight response)
# ============================================================================


class SpaceOrganizationV2Serializer(serializers.Serializer):
    """Minimal organization info for external API"""

    name = serializers.CharField()
    domain_handle = serializers.CharField()


class SpaceListV2Serializer(serializers.ModelSerializer):
    """
    Lightweight Space serializer for API v2 Platform.
    Returns only essential fields - no sensitive data like users, roles, permissions.
    """

    logo = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()

    class Meta:
        model = Space
        fields = [
            "name",
            "slug",
            "token",
            "description",
            "logo",
            "privacy_type",
            "space_type",
            "content_type",
            "organization",
        ]

    def get_logo(self, obj):
        if obj.logo:
            return imagekitBackend.generateURL(obj.logo.name)
        return None

    def get_organization(self, obj):
        if obj.space_organization:
            return {
                "name": obj.space_organization.name,
                "domain_handle": obj.space_organization.domain_handle,
            }
        return None


class SpaceDetailV2Serializer(serializers.ModelSerializer):
    """
    Space detail serializer for API v2 Platform.
    Returns essential fields + basic organization info.
    No sensitive data like users, roles, permissions, access_requests.
    """

    logo = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()
    agents = serializers.SerializerMethodField()

    class Meta:
        model = Space
        fields = [
            "name",
            "slug",
            "token",
            "description",
            "logo",
            "privacy_type",
            "space_type",
            "content_type",
            "organization",
            "agents",
            "created",
            "modified",
        ]

    def get_logo(self, obj):
        if obj.logo:
            return imagekitBackend.generateURL(obj.logo.name)
        return None

    def get_organization(self, obj):
        if obj.space_organization:
            return {
                "name": obj.space_organization.name,
                "domain_handle": obj.space_organization.domain_handle,
            }
        return None

    def get_agents(self, obj):
        """Return basic info about agents (pilots) linked to this space"""
        from unpod.core_components.models import Pilot

        pilots = Pilot.objects.filter(space=obj)
        if not pilots.exists():
            return []
        return [
            {
                "name": pilot.name,
                "handle": pilot.handle,
                "type": pilot.type,
            }
            for pilot in pilots
        ]


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Space List Response",
            value={
                "status_code": 200,
                "message": "Spaces fetched successfully",
                "count": 2,
                "data": [
                    {
                        "name": "My Workspace",
                        "slug": "my-workspace",
                        "token": "abc123def456",
                        "description": "Main workspace for AI agents",
                        "logo": "https://ik.imagekit.io/...",
                        "privacy_type": "private",
                        "space_type": "general",
                        "content_type": "general",
                        "organization": {
                            "name": "Acme Corp",
                            "domain_handle": "acme-corp",
                        },
                    }
                ],
            },
            response_only=True,
        )
    ]
)
class SpaceListResponseV2Serializer(serializers.Serializer):
    """Response schema for GET /api/v2/platform/spaces/"""

    status_code = serializers.IntegerField()
    message = serializers.CharField()
    count = serializers.IntegerField()
    data = SpaceListV2Serializer(many=True)


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Space Detail Response",
            value={
                "status_code": 200,
                "message": "Space fetched successfully",
                "data": {
                    "name": "My Workspace",
                    "slug": "my-workspace",
                    "token": "abc123def456",
                    "description": "Main workspace for AI agents",
                    "logo": "https://ik.imagekit.io/...",
                    "privacy_type": "private",
                    "space_type": "general",
                    "content_type": "general",
                    "organization": {
                        "name": "Acme Corp",
                        "domain_handle": "acme-corp",
                    },
                    "agents": [
                        {
                            "name": "HR Recruiter",
                            "handle": "hr-recruiter-bot",
                            "type": "voice",
                        }
                    ],
                    "created": "2025-01-15T10:30:00Z",
                    "modified": "2025-01-20T14:45:00Z",
                },
            },
            response_only=True,
        )
    ]
)
class SpaceDetailResponseV2Serializer(serializers.Serializer):
    """Response schema for GET /api/v2/platform/spaces/<token>/"""

    status_code = serializers.IntegerField()
    message = serializers.CharField()
    data = SpaceDetailV2Serializer()
