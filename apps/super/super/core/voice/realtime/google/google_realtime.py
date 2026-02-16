from livekit.agents import types
import os
import weakref
from google.genai import types
from livekit.agents import llm
from livekit.plugins.google.tools import _LLMTool
from livekit.agents.types import (
    DEFAULT_API_CONNECT_OPTIONS,
    NOT_GIVEN,
    APIConnectOptions,
    NotGivenOr,
)
from livekit.agents.utils import images, is_given
from livekit.plugins.google.beta.realtime.api_proto import (
    LiveAPIModels,
    Voice,
)

from livekit.plugins.google.beta.realtime.realtime_api import (
    _RealtimeOptions,
    RealtimeSession,
)


class UnpodGoogleRealtime(llm.RealtimeModel):
    def __init__(
        self,
        *,
        instructions: NotGivenOr[str] = NOT_GIVEN,
        model: NotGivenOr[LiveAPIModels | str] = NOT_GIVEN,
        api_key: NotGivenOr[str] = NOT_GIVEN,
        voice: Voice | str = "Puck",
        language: NotGivenOr[str] = NOT_GIVEN,
        modalities: NotGivenOr[list[types.Modality]] = NOT_GIVEN,
        vertexai: NotGivenOr[bool] = NOT_GIVEN,
        project: NotGivenOr[str] = NOT_GIVEN,
        location: NotGivenOr[str] = NOT_GIVEN,
        candidate_count: int = 1,
        temperature: NotGivenOr[float] = NOT_GIVEN,
        max_output_tokens: NotGivenOr[int] = NOT_GIVEN,
        top_p: NotGivenOr[float] = NOT_GIVEN,
        top_k: NotGivenOr[int] = NOT_GIVEN,
        presence_penalty: NotGivenOr[float] = NOT_GIVEN,
        frequency_penalty: NotGivenOr[float] = NOT_GIVEN,
        input_audio_transcription: NotGivenOr[
            types.AudioTranscriptionConfig | None
        ] = NOT_GIVEN,
        output_audio_transcription: NotGivenOr[
            types.AudioTranscriptionConfig | None
        ] = NOT_GIVEN,
        image_encode_options: NotGivenOr[images.EncodeOptions] = NOT_GIVEN,
        enable_affective_dialog: NotGivenOr[bool] = NOT_GIVEN,
        proactivity: NotGivenOr[bool] = NOT_GIVEN,
        realtime_input_config: NotGivenOr[types.RealtimeInputConfig] = NOT_GIVEN,
        context_window_compression: NotGivenOr[
            types.ContextWindowCompressionConfig
        ] = NOT_GIVEN,
        api_version: NotGivenOr[str] = NOT_GIVEN,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
        http_options: NotGivenOr[types.HttpOptions] = NOT_GIVEN,
        _gemini_tools: NotGivenOr[list[_LLMTool]] = NOT_GIVEN,
    ) -> None:
        if not is_given(input_audio_transcription):
            input_audio_transcription = types.AudioTranscriptionConfig()
        if not is_given(output_audio_transcription):
            output_audio_transcription = types.AudioTranscriptionConfig()

        server_turn_detection = True
        if (
            is_given(realtime_input_config)
            and realtime_input_config.automatic_activity_detection
            and realtime_input_config.automatic_activity_detection.disabled
        ):
            server_turn_detection = False

        super().__init__(
            capabilities=llm.RealtimeCapabilities(
                message_truncation=False,
                turn_detection=server_turn_detection,
                user_transcription=input_audio_transcription is not None,
                auto_tool_reply_generation=True,
                audio_output=True,
                manual_function_calls=False,
            )
        )

        if not is_given(model):
            if vertexai:
                model = "gemini-2.0-flash-exp"
            else:
                model = "gemini-2.0-flash-live-001"

        gemini_api_key = (
            api_key if is_given(api_key) else os.environ.get("GOOGLE_API_KEY")
        )
        gcp_project = (
            project if is_given(project) else os.environ.get("GOOGLE_CLOUD_PROJECT")
        )
        gcp_location: str | None = (
            location
            if is_given(location)
            else os.environ.get("GOOGLE_CLOUD_LOCATION") or "asia-south1"
        )
        use_vertexai = (
            vertexai
            if is_given(vertexai)
            else os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "0").lower()
            in ["true", "1"]
        )

        if use_vertexai:
            if not gcp_project or not gcp_location:
                raise ValueError(
                    "Project is required for VertexAI via project kwarg or GOOGLE_CLOUD_PROJECT environment variable"  # noqa: E501
                )
            gemini_api_key = None  # VertexAI does not require an API key
        else:
            gcp_project = None
            gcp_location = None
            if not gemini_api_key:
                raise ValueError(
                    "API key is required for Google API either via api_key or GOOGLE_API_KEY environment variable"  # noqa: E501
                )

        self._opts = _RealtimeOptions(
            model=model,
            api_key=gemini_api_key,
            voice=voice,
            response_modalities=modalities,
            vertexai=use_vertexai,
            project=gcp_project,
            location=gcp_location,
            candidate_count=candidate_count,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            top_p=top_p,
            top_k=top_k,
            presence_penalty=presence_penalty,
            frequency_penalty=frequency_penalty,
            instructions=instructions,
            input_audio_transcription=input_audio_transcription,
            output_audio_transcription=output_audio_transcription,
            language=language,
            image_encode_options=image_encode_options,
            enable_affective_dialog=enable_affective_dialog,
            proactivity=proactivity,
            realtime_input_config=realtime_input_config,
            context_window_compression=context_window_compression,
            api_version=api_version,
            gemini_tools=_gemini_tools,
            conn_options=conn_options,
            http_options=http_options,
        )

        self._sessions = weakref.WeakSet[RealtimeSession]()

    def session(self) -> RealtimeSession:
        sess = RealtimeSession(self)
        self._sessions.add(sess)
        return sess

    def update_options(
        self,
        *,
        voice: NotGivenOr[str] = NOT_GIVEN,
        temperature: NotGivenOr[float] = NOT_GIVEN,
    ) -> None:
        """
        Update the options for the RealtimeModel.

        Args:
            voice (str, optional): The voice to use for the session.
            temperature (float, optional): The temperature to use for the session.
            tools (list[LLMTool], optional): The tools to use for the session.
        """
        if is_given(voice):
            self._opts.voice = voice

        if is_given(temperature):
            self._opts.temperature = temperature

        for sess in self._sessions:
            sess.update_options(
                voice=self._opts.voice,
                temperature=self._opts.temperature,
            )

    async def aclose(self) -> None:
        pass
