from import_export import resources
from .models import VoiceProfiles


class VoiceProfilesResource(resources.ModelResource):
    class Meta:
        model = VoiceProfiles
        import_id_fields = ["agent_profile_id"]  # ✅ use your PK field
        fields = (
            "agent_profile_id",
            "name",
            "llm_provider",
            "llm_model",
            "stt_provider",
            "stt_model",
            "tts_language",
            "tts_provider",
            "tts_model",
            "tts_voice",
            # "first_message",
            "greeting_message",
            "temperature",
            "gender",
            "quality",
            "estimated_cost",
            "description",
            "voice_speed",
            "chat_model",
        )
        skip_unchanged = True
        report_skipped = True
