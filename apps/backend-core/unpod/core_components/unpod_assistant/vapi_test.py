import requests
import logging
from typing import Optional, Any, Dict
from .Agent_Enum import (
    OPENAI_MODEL,
    OPENAI_TRANSCRIBER,
    OPENAI_VOICE_ID,
    GOOGLE_TRANSCRIBERS,
    ELVENLABS_MODELS,
    DEEPGRAM_VOICE_ID,
    LLM_PROVIDER,
    STT_PROVIDER,
    TTS_PROVIDER,
    LLM_MODEL_MAP,
    REALTIME_LLM_CONFIG,
    DEFAULT_TTS_VOICES,
    TRANSCRIBER_MODEL_MAP,
)
import os
import sys
import django

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()
from django.conf import settings


class VapiAssistant:
    def __init__(self):
        self.api_key = settings.VAPI_API_KEY
        self.vapi_url = f"{settings.VAPI_URL}/assistant"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        self.model_config = {}
        self.assistant_id: Optional[str] = None
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        )
        self.logging = logging.getLogger("VapiAssistant")
        self.agent_exist = False

    def base_url_call(self, assistant_id: Optional[str] = None) -> None:
        if self.assistant_id:
            res = self.get_assistant()
            if res.status_code != 200:
                self.assistant_id = None
                self.logging.error("assistant not found in VAPI creating new assistant")
        return self.upsert()

    def create_config(self, model_config: dict) -> dict:
        """
        Creates a configuration for vapi agent that can be passed to create or update vapi assistant
        """

        self.agent_name = (
            model_config.get("name") or f'UnpodAi_{model_config.get("space_token")}'
        )

        self.space_token = model_config.get("space_token") or ""

        if model_config.get("llm_model") in LLM_MODEL_MAP:
            llm_model = LLM_MODEL_MAP[model_config["llm_model"]]
            model_config["llm_model"] = getattr(llm_model, "value", llm_model)

        if model_config["llm_provider"] in REALTIME_LLM_CONFIG:
            config = REALTIME_LLM_CONFIG[model_config["llm_provider"]]
            return {
                "model": {
                    "provider": config["provider"],
                    "model": config["model"],
                    "temperature": model_config.get("temperature", 0.3),
                    "systemPrompt": model_config.get("system_prompt", "default"),
                },
                "name": self.agent_name,
                "firstMessage": model_config.get(
                    "first_message", "Hello, how can I help you?"
                ),
            }

        tts_provider = model_config.get("tts_provider", "openai")
        tts_voice = model_config.get("tts_voice", "")
        voice_id = tts_voice

        if tts_provider == "openai":
            voice_id = (
                tts_voice
                if tts_voice in OPENAI_VOICE_ID._value2member_map_
                else DEFAULT_TTS_VOICES["openai"]
            )

        elif tts_provider == "deepgram":
            # Normalize voice_id format
            model_config["stt_language"] = "en"
            voice_id = tts_voice.split("-")[1] if "-" in tts_voice else tts_voice
            voice_id = (
                voice_id
                if voice_id in DEEPGRAM_VOICE_ID._value2member_map_
                else DEFAULT_TTS_VOICES["deepgram"]
            )

        if model_config["stt_provider"] in TRANSCRIBER_MODEL_MAP:
            if model_config["stt_provider"] == "openai":
                if (
                    model_config["stt_model"]
                    not in OPENAI_TRANSCRIBER._value2member_map_
                ):
                    model_config["stt_model"] = OPENAI_TRANSCRIBER.GPT_4o
            else:
                stt_model = TRANSCRIBER_MODEL_MAP[model_config["stt_provider"]]
                model_config["stt_model"] = getattr(stt_model, "value", stt_model)

        if model_config.get("tts_provider") == "elevenlabs":
            model_config["tts_provider"] = ELVENLABS_MODELS.ELEVENLABS.value

        if model_config.get("stt_provider") == "elevenlabs":
            model_config["stt_provider"] = ELVENLABS_MODELS.ELEVENLABS.value

        if model_config.get("tts_provider") == "unpod":
            model_config["tts_provider"] = "vapi"

        if model_config.get("stt_provider") == STT_PROVIDER.GOOGLE:
            stt_model = model_config.get("stt_model")
            model_config["stt_model"] = (
                stt_model
                if stt_model in GOOGLE_TRANSCRIBERS._value2member_map_
                else GOOGLE_TRANSCRIBERS.GEMINI_FLASH.value
            )
            language = "Hindi" if model_config["stt_language"] == "hi" else "English"
            model_config["stt_language"] = language
        voice_data = {"provider": model_config["tts_provider"], "voiceId": voice_id}

        if model_config["tts_provider"] != "vapi":
            voice_data["model"] = model_config["tts_model"]

        # Add language for TTS providers that support it
        tts_language = model_config.get("tts_language", "en")

        # Map language codes to provider-specific formats
        # en_hi (multilingual) maps to "hi" for Cartesia as it handles mixed content in Hindi mode
        language_map = {
            "en": "en",
            "hi": "hi",
            "en_hi": "hi",  # Multilingual - use Hindi for mixed en-hi content
        }

        if model_config["tts_provider"] == "cartesia":
            voice_data["language"] = language_map.get(tts_language, "en")

        return {
            "transcriber": {
                "provider": model_config["stt_provider"],
                "model": model_config.get("stt_model")
                if model_config.get("stt_provider") != "speechmatics"
                else "default",
                "language": model_config["stt_language"],
            },
            "model": {
                "provider": model_config["llm_provider"]
                if model_config["llm_provider"] != "gemini"
                else "google",
                "model": model_config["llm_model"],
                "temperature": model_config.get("temperature") or 0.3,
                "systemPrompt": model_config.get("system_prompt") or "default",
            },
            "voice": voice_data,
            "name": self.agent_name,
            "firstMessage": model_config.get("first_message")
            or "Hello, how can I help you?",
            "stopSpeakingPlan": {
                "numWords": model_config.get("number_of_words"),
                "voiceSeconds": model_config.get("voice_seconds"),
                "backoffSeconds": model_config.get("back_off_seconds"),
            },
        }

    def default_config(self):
        return {
            "transcriber": {
                "provider": "deepgram",
                "model": "nova-3",
                "language": "en",
            },
            "model": {
                "provider": "openai",
                "model": "gpt-4o-mini",
                "temperature": 0.3,
                "systemPrompt": self.model_config.get("system_prompt"),
            },
            "voice": {"provider": "vapi", "voiceId": "Neha"},
            "name": self.agent_name,
            "firstMessage": self.model_config.get("first_message", "hello"),
        }

    def get_assistant(self) -> requests.Response:
        """
        Used to fetch details of a vapi assistant from api
        """
        response = requests.get(
            f"{self.vapi_url}/{self.assistant_id}", headers=self.headers
        )
        if response.status_code != 200:
            self.agent_exist = False
        else:
            self.agent_exist = True
        return response

    def list_assistants(self) -> requests.Response:
        """
        list down all the available vapi assistants
        """
        response = requests.get(f"{self.vapi_url}", headers=self.headers)

        for i in response.json():
            print(f" \n\n {i.get('name')}  : -- \n\n {i}")
        return response

    def delete_assistant(self, assistant_id: Optional[str] = None):
        """
        delte the vapi assistant
        """
        if assistant_id:
            self.assistant_id = assistant_id

        response = requests.delete(
            f"{self.vapi_url}/{self.assistant_id}", headers=self.headers
        )
        self.logging.info(f"\n =======deleted assistant======  {response}\n")
        return response

    def default_asistant(self):
        self.model_config["llm_provider"] = LLM_PROVIDER.OPENAI
        self.model_config["llm_model"] = OPENAI_MODEL.GPT_4o
        self.model_config["stt_provider"] = STT_PROVIDER.OPENAI
        self.model_config["stt_model"] = OPENAI_TRANSCRIBER.GPT_4o
        self.model_config["tts_provider"] = TTS_PROVIDER.OPENAI
        self.model_config["tts_voice"] = OPENAI_VOICE_ID.ALLOY

        return self.model_config

    def upsert(self, model_configs: Optional[Dict[str, Any]] = None) -> dict:
        """
        used to create and update vapi assistant based on the configs passed
        """

        if model_configs is not None:
            self.model_config = model_configs
            self.assistant_id = self.model_config.get("assistant_id") or None
            self.get_assistant()

        # if agent exist true update the existing agent else create new agent
        if self.agent_exist:
            response = requests.patch(
                f"{self.vapi_url}/{self.assistant_id}",
                headers=self.headers,
                json=self.create_config(self.model_config),
            )

        else:
            response = requests.post(
                f"{self.vapi_url}",
                headers=self.headers,
                json=self.create_config(self.model_config),
            )

        # checking for response code whether the api request was successful or not

        if response.status_code == 200:
            self.logging.info(f"assistant updated {response}")
            return response.json()["id"]

        elif response.status_code == 201:
            self.assistant_id = response.json()["id"]
            self.logging.info(f"assistant created {self.assistant_id}")
            return response.json()["id"]

        # creating default agent in case of any error

        else:
            if self.agent_exist:
                self.logging.error(f"error updating agent")
                response = requests.patch(
                    f"{self.vapi_url}/{self.assistant_id}",
                    headers=self.headers,
                    json=self.default_config(),
                )
                return self.assistant_id

            self.logging.error(f"Creating a default assistant {response}")
            self.default_asistant()

            response = requests.post(
                f"{self.vapi_url}",
                headers=self.headers,
                json=self.default_config(),
            )
            self.logging.info(f"default assistant created {response.json()}")

            if response.status_code == 201:
                return response.json()["id"]
            else:
                return ""

    def create_vapi_assistant(
        self, model_configs: Optional[Dict[str, Any]] = None
    ) -> None:
        self.model_config = model_configs
        self.assistant_id = self.model_config.get("assistant_id", "") or None
        return self.base_url_call(self.assistant_id)
