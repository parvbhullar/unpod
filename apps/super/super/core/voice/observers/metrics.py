from pipecat.frames.frames import (
    MetricsFrame,
    UserStartedSpeakingFrame,
    UserStoppedSpeakingFrame,
)

from pipecat.observers.base_observer import BaseObserver, FramePushed
from pipecat.metrics.metrics import (
    LLMUsageMetricsData,
    ProcessingMetricsData,
    TTFBMetricsData,
    TTSUsageMetricsData,
    LLMTokenUsage,
)
from datetime import datetime

from pipecat.observers.turn_tracking_observer import TurnTrackingObserver

from super.core.resource.model_providers.contants import (
    AIModelName,
    # OPEN_AI_LANGUAGE_MODELS,
    # ANTHROPIC_LANGUAGE_MODELS,
    # GROQ_LANGUAGE_MODELS,
    AI_MODELS,
    VOICE_MODEL_PRICING,
)

from pipecat.frames.frames import (
    BotStartedSpeakingFrame,
    BotStoppedSpeakingFrame,
    CancelFrame,
    EndFrame,
    StartFrame,
    UserStartedSpeakingFrame,
    UserStoppedSpeakingFrame,
)
import asyncio
from collections import deque
from typing import Deque
from statistics import  mean

cost = {
    "llm": {
        "prompt_token_cost": 1.10,
        "completion_token_cost": 4.40,
        "per_token": 1000000,
    },
    "stt": {"audio_cost": 0.006, "audio_per": 60},
    "tts": {"audio_cost": 15, "character_per": 1000000},
}


class CustomMetricObserver(BaseObserver):
    def __init__(self, user_state, **kwargs):
        super().__init__(**kwargs)
        self.user_state = user_state
        self.tts_char = 0
        self.llm_prompt = 0
        self.llm_comp = 0

        self.curr_prompt = 0
        self.curr_comp = 0

        self.stt_start = None
        self.stt_end = None
        self.llm = []
        self.stt = [0]
        self.tts = []
        self.llm_model = ""
        self.tts_model = ""
        self.stt_model = ""
        self.curr_stt=0
        self.curr_tts=None
        self.curr_llm=None
        self.curr_total=None

    async def on_push_frame(self, data: FramePushed):
        self.stt_start=None
        self.stt_end=None

        # Per-turn tracking - start from 1 to match TurnTrackingObserver
        self.current_turn_number = 1
        self.turn_metrics = {}  # Dictionary to store per-turn metrics
        self._initialize_turn_metrics()

    async def on_push_frame(
        self,
        data:FramePushed
    ):
        if isinstance(data.frame, MetricsFrame):
            await self._handle_metrics(data.frame)
            await self.calculate_latency(data.frame)

        if isinstance(data.frame, UserStartedSpeakingFrame):
            self.stt_start = datetime.now()
        if isinstance(data.frame, UserStoppedSpeakingFrame):
            self.stt_end = datetime.now()

    async def _handle_metrics(self, frame: MetricsFrame):
        metrics = {}
        for d in frame.data:
            if isinstance(d, TTFBMetricsData):
                if "ttfb" not in metrics:
                    metrics["ttfb"] = []
                metrics["ttfb"].append(d.model_dump(exclude_none=True))
            elif isinstance(d, ProcessingMetricsData):
                if "processing" not in metrics:
                    metrics["processing"] = []
                metrics["processing"].append(d.model_dump(exclude_none=True))
            elif isinstance(d, LLMUsageMetricsData):
                if "tokens" not in metrics:
                    metrics["tokens"] = []
                metrics["tokens"].append(d.value.model_dump(exclude_none=True))
            elif isinstance(d, TTSUsageMetricsData):
                if "characters" not in metrics:
                    metrics["characters"] = []
                metrics["characters"].append(d.model_dump(exclude_none=True))
            elif isinstance(d, LLMTokenUsage):
                metrics["data"].append(d.model_dump(exclude_none=True))

        self.metrics_cost(metrics)
        # self.create_usage(metrics)

    def create_usage(self, metrics):
        usage = self.user_state.usage
        if "characters" in metrics:
            ele = metrics["characters"][0]
            if "tts" in ele["processor"].lower():
                self.tts_char = ele["value"]
            tts_cost = (
                cost["tts"]["audio_cost"] * self.tts_char / cost["tts"]["character_per"]
            )
            usage["costs"]["tts_cost"] += tts_cost

        elif "tokens" in metrics:
            ele = metrics["tokens"][0]
            self.llm_prompt = ele["prompt_tokens"]
            self.llm_comp = ele["completion_tokens"]
            llm_cost = (
                cost["llm"]["prompt_token_cost"]
                * self.llm_prompt
                / cost["llm"]["per_token"]
            ) + (
                cost["llm"]["completion_token_cost"]
                * self.llm_comp
                / cost["llm"]["per_token"]
            )
            usage["costs"]["llm_cost"] += llm_cost

        if self.stt_start and self.stt_end:
            duration = (self.stt_end - self.stt_start).total_seconds()
            stt_cost = cost["stt"]["audio_cost"] * duration / cost["stt"]["audio_per"]
            usage["costs"]["stt_cost"] += stt_cost
            self.stt_start = None
            self.stt_end = None

        usage["total_cost"] = (
            usage["costs"]["llm_cost"]
            + usage["costs"]["tts_cost"]
            + usage["costs"]["stt_cost"]
        )
        self.user_state.usage = usage

    def safe_ai_model(self, value: str):
        """Safely get AIModelName enum from string value."""
        try:
            return AIModelName(value)
        except ValueError:
            return None

    def get_model_pricing(self, model: AIModelName):
        """Get pricing information for a model from constants.

        Returns dict with pricing info, or None if model not found in constants.
        For language models, converts to per-token pricing format.
        For voice models (STT/TTS), returns audio/character pricing.
        """
        # Check if it's a language model first
        model_info = AI_MODELS.get(model)

        if model_info:
            # Language model - return token-based pricing
            return {
                "prompt_token_cost": model_info.prompt_token_cost,
                "completion_token_cost": model_info.completion_token_cost,
                "max_tokens": 1000000,
            }

        # For voice models (STT/TTS), we need a separate pricing structure
        # Since voice models don't use LanguageModelProviderModelInfo,
        # we'll maintain backward compatibility with a default structure
        return None

    def _initialize_turn_metrics(self):
        """Initialize metrics for the current turn"""
        turn_key = f"turn_{self.current_turn_number}"
        self.turn_metrics[turn_key] = {
            "turn_number": self.current_turn_number,
            "costs": {
                "llm_cost": 0.0,
                "stt_cost": 0.0,
                "tts_cost": 0.0
            },
            "usage": {
                "llm_prompt_tokens": 0,
                "llm_completion_tokens": 0,
                "stt_duration": 0.0,
                "tts_characters": 0
            },
            "latencies": {
                "llm_latency": 0.0,
                "stt_latency": 0.0,
                "tts_latency": 0.0
            },
            "ttfb": {
                "llm_ttfb": 0.0,
                "stt_ttfb": 0.0,
                "tts_ttfb": 0.0
            }
        }

    def increment_turn(self):
        """Increment turn number and initialize metrics for new turn"""
        self.current_turn_number += 1
        self._initialize_turn_metrics()

    def get_turn_metrics(self, turn_number: int = None):
        """Get metrics for a specific turn or current turn"""
        if turn_number is None:
            turn_number = self.current_turn_number
        turn_key = f"turn_{turn_number}"
        return self.turn_metrics.get(turn_key, {})

    def get_all_turn_metrics(self):
        """Get metrics for all turns"""
        return self.turn_metrics

    def metrics_cost(self, metrics):
        try:
            usage = self.user_state.usage
            llm = usage.get("llm_provider") + "_" + usage.get("llm_model")
            llm_model = (
                self.safe_ai_model(llm)
                if self.safe_ai_model(llm)
                else AIModelName.OPENAI_GPT4_O
            )
            stt = usage.get("stt_provider") + "_" + usage.get("stt_model")
            stt_model = (
                self.safe_ai_model(stt)
                if self.safe_ai_model(stt)
                else AIModelName.DEEPGRAM_NOVA_2_GENERAL
            )
            tts = usage.get("tts_provider") + "_" + usage.get("tts_model")
            tts_model = (
                self.safe_ai_model(tts)
                if self.safe_ai_model(tts)
                else AIModelName.DEEPGRAM_AURA_LUNA_EN
            )

            # Get pricing from constants (fallback to defaults if not found)
            stt_price = self.get_voice_model_pricing(stt_model, "stt")
            tts_price = self.get_voice_model_pricing(tts_model, "tts")

            # Get current turn metrics
            turn_key = f"turn_{self.current_turn_number}"
            if turn_key not in self.turn_metrics:
                self._initialize_turn_metrics()
            turn_data = self.turn_metrics[turn_key]

            # Extract TTFB from metrics
            if "ttfb" in metrics:
                # Time To First Byte - separate by processor type
                for ttfb_data in metrics["ttfb"]:
                    if "value" in ttfb_data:
                        ttfb_value = ttfb_data["value"]  # TTFB in seconds
                        ttfb_ms = ttfb_value * 1000  # Convert to milliseconds for latency
                        processor_name = ttfb_data.get("processor", "").lower()

                        # Check STT first (before TTS) because "sttservice" contains "tts" as substring
                        if "sttservice" in processor_name or "transcription" in processor_name:
                            turn_data["ttfb"]["stt_ttfb"] += ttfb_value
                            turn_data["latencies"]["stt_latency"] += ttfb_ms
                        elif "llmservice" in processor_name or "openai" in processor_name or "anthropic" in processor_name or "groq" in processor_name:
                            turn_data["ttfb"]["llm_ttfb"] += ttfb_value  # Store in seconds
                            turn_data["latencies"]["llm_latency"] += ttfb_ms  # Store in ms
                        elif "ttsservice" in processor_name or "cartesia" in processor_name or "elevenlabs" in processor_name or "xtts" in processor_name:
                            turn_data["ttfb"]["tts_ttfb"] += ttfb_value
                            turn_data["latencies"]["tts_latency"] += ttfb_ms
                        else:
                            # Default to LLM for unknown processors
                            turn_data["ttfb"]["llm_ttfb"] += ttfb_value
                            turn_data["latencies"]["llm_latency"] += ttfb_ms

            if "processing" in metrics:
                # Processing time - can be for STT or TTS
                for proc_data in metrics["processing"]:
                    processor_name = proc_data.get("processor", "").lower()
                    if "value" in proc_data:
                        if "stt" in processor_name or "transcription" in processor_name:
                            turn_data["latencies"]["stt_latency"] += proc_data["value"]
                        elif "tts" in processor_name or "synthesis" in processor_name:
                            turn_data["latencies"]["tts_latency"] += proc_data["value"]

            # Track TTS costs and usage
            if "characters" in metrics:
                ele = metrics["characters"][0]
                ele = metrics['characters'][0]
                if "tts" in ele["processor"].lower():
                    self.tts_char = ele["value"]
                tts_cost = (
                    tts_price.get("audio_cost", 0.18)
                    * self.tts_char
                    / tts_price.get("character_per", 10000)
                )
                usage["costs"]["tts_cost"] = (
                    usage.get("costs", {}).get("tts_cost", 0) + tts_cost
                )
                usage["tts_characters_count"] = (
                    usage.get("tts_characters_count", 0) + self.tts_char
                )
                tts_cost = tts_price.get("audio_cost", 0.18) * self.tts_char / tts_price.get("character_per", 10000)

                # Aggregate usage
                usage["costs"]["tts_cost"] = usage.get("costs", {}).get("tts_cost", 0) + tts_cost
                usage["tts_characters_count"] = usage.get("tts_characters_count", 0) + self.tts_char

                # Per-turn tracking
                turn_data["costs"]["tts_cost"] += tts_cost
                turn_data["usage"]["tts_characters"] += self.tts_char

            # Track LLM costs and usage
            if "tokens" in metrics:
                ele = metrics["tokens"][0]
                self.llm_prompt = ele["prompt_tokens"]
                self.llm_comp = ele["completion_tokens"]

                # Get LLM pricing from constants
                llm_price = self.get_model_pricing(llm_model)
                if not llm_price:
                    llm_price = {
                        "prompt_token_cost": 2,
                        "completion_token_cost": 8,
                        "max_tokens": 1000000,
                    }

                llm_prompt_cost = (
                    llm_price["prompt_token_cost"]
                    / llm_price.get("max_tokens", 10000000)
                    * self.llm_prompt
                )
                llm_complete = (
                    llm_price["completion_token_cost"]
                    / llm_price.get("max_tokens", 10000000)
                    * self.llm_comp
                )

                llm_cost = llm_complete + llm_prompt_cost
                usage["llm_prompt_tokens"] = (
                    usage.get("llm_prompt_tokens", 0) + self.llm_prompt
                )
                usage["llm_completion_tokens"] = (
                    usage.get("llm_completion_tokens", 0) + self.llm_comp
                )
                usage["costs"]["llm_cost"] = (
                    usage.get("costs", {}).get("llm_cost", 0) + llm_cost
                )

                # Aggregate usage
                usage["llm_prompt_tokens"] = usage.get("llm_prompt_tokens", 0) + self.llm_prompt
                usage["llm_completion_tokens"] = usage.get("llm_completion_tokens", 0) + self.llm_comp
                usage["costs"]["llm_cost"] = usage.get("costs", {}).get("llm_cost", 0) + llm_cost

                # Per-turn tracking
                turn_data["costs"]["llm_cost"] += llm_cost
                turn_data["usage"]["llm_prompt_tokens"] += self.llm_prompt
                turn_data["usage"]["llm_completion_tokens"] += self.llm_comp

            # Track STT costs and usage
            if self.stt_start and self.stt_end:
                duration = (self.stt_end - self.stt_start).total_seconds()

                # Ensure duration is positive (handle edge cases where timestamps might be out of order)
                if duration < 0:
                    duration = abs(duration)

                # Skip if duration is unreasonably long (more than 5 minutes for a single STT segment)
                if duration > 300:
                    duration = 0

                stt_cost = stt_price.get("audio_cost", 0.08) * duration / stt_price.get("audio_per", 60)

                # Calculate STT latency (time between start and end)
                stt_latency_ms = duration * 1000  # Convert to milliseconds

                # Aggregate usage
                usage["stt_audio_duration"] = usage.get("stt_audio_duration", 0) + duration
                usage["costs"]["stt_cost"] = usage.get("costs", {}).get("stt_cost", 0) + stt_cost

                # Per-turn tracking
                turn_data["costs"]["stt_cost"] += stt_cost
                turn_data["usage"]["stt_duration"] += duration
                if turn_data["latencies"]["stt_latency"] == 0:  # Only set if not already set from processing metrics
                    turn_data["latencies"]["stt_latency"] = stt_latency_ms

            if self.stt_start and self.stt_end and (self.stt_start < self.stt_end):
                duration = abs(self.stt_end - self.stt_start).total_seconds()
                stt_cost = (
                    stt_price.get("audio_cost", 0.08)
                    * duration
                    / stt_price.get("audio_per", 60)
                )
                usage["stt_audio_duration"] = (
                    usage.get("stt_audio_duration", 0) + duration
                )
                usage["costs"]["stt_cost"] = (
                    usage.get("costs", {}).get("stt_cost", 0) + stt_cost
                )
                self.stt_start = None
                self.stt_end = None

            # Ensure costs dict exists
            if "costs" not in usage:
                usage["costs"] = {}

            llm_cost = usage.get("costs", {}).get("llm_cost", 0)
            tts_cost = usage.get("costs", {}).get("tts_cost", 0)
            stt_cost = usage.get("costs", {}).get("stt_cost", 0)
            usage["total_cost"] = llm_cost + tts_cost + stt_cost

            self.user_state.usage = usage
        except Exception as e:
            pass

    def get_voice_model_pricing(self, model: AIModelName, model_type: str):
        """Get voice model pricing (STT/TTS) from constants with fallback defaults.

        Args:
            model: The AI model enum
            model_type: Either 'stt' or 'tts'

        Returns:
            Dict with pricing information
        """
        # Default pricing based on model type
        defaults = {
            "stt": {"audio_cost": 0.006, "audio_per": 60},
            "tts": {"audio_cost": 5, "character_per": 1000000},
        }

        # Get pricing from constants.py, fallback to defaults if not found
        return VOICE_MODEL_PRICING.get(model, defaults.get(model_type, {}))

    async def calculate_latency(self,frame):

        if not isinstance(self.user_state.extra_data,dict):
            self.user_state.extra_data = {}

        if not self.user_state.extra_data.get('provider'):
            self.user_state.extra_data["provider"] = "pipecat"

        latency_metrics = self.user_state.extra_data.get("latency_metrics", [])
        metric_entry = {}
        metrics = {}

        for d in frame.data:
            if isinstance(d, TTFBMetricsData):
                if "ttfb" not in metrics:
                    metrics["ttfb"] = []
                metrics["ttfb"].append(d.model_dump(exclude_none=True))
            elif isinstance(d, ProcessingMetricsData):
                if "processing" not in metrics:
                    metrics["processing"] = []
                metrics["processing"].append(d.model_dump(exclude_none=True))
            elif isinstance(d, LLMUsageMetricsData):
                if "tokens" not in metrics:
                    metrics["tokens"] = []
                metrics["tokens"].append(d.value.model_dump(exclude_none=True))

            elif isinstance(d, TTSUsageMetricsData):
                if "characters" not in metrics:
                    metrics["characters"] = []
                metrics["characters"].append(d.model_dump(exclude_none=True))

        if "ttfb" in metrics:
            ele = metrics['ttfb'][0]
            if "llm" in ele["processor"].lower():
                self.llm_model = ele["processor"]
                self.llm.append(ele["value"])
                self.curr_llm=ele["value"]
            if "tts" in ele["processor"].lower():
                self.tts_model = ele["processor"]
                self.tts.append(ele["value"])
                self.curr_tts=ele["value"]
            if "stt" in ele["processor"].lower():
                self.stt_model = ele["processor"]
                self.stt.append(ele["value"])
                self.curr_stt=ele["value"]


        if "tokens" in metrics:
            ele = metrics["tokens"][0]
            self.curr_prompt = ele["prompt_tokens"]
            self.curr_comp = ele["completion_tokens"]

        if self.curr_llm and self.curr_tts and self.curr_stt:
            self.curr_total=self.curr_llm + self.curr_tts + self.curr_stt

            metric_entry={
                "llm_latency": self.curr_llm,
                "tts_latency": self.curr_tts,
                "stt_latency": self.curr_stt,
                "total_latency": self.curr_total,
            }


            if self.llm and self.tts and self.stt:
                stt_latency = mean(self.stt)
                llm_latency = mean(self.llm)
                tts_latency = mean(self.tts)

                total_latency = stt_latency + llm_latency + tts_latency

                data = {
                    "avg_llm_latency": llm_latency,
                    "avg_stt_latency": stt_latency,
                    "avg_tts_latency": tts_latency,
                    "avg_total_latency": total_latency
                }

                metric_entry.update(data)

            if self.curr_comp and self.curr_prompt:


                metric_entry.update({
                    "prompt_tokens": self.curr_prompt,
                    "completion_tokens": self.curr_comp,
                })

                self.curr_prompt=0
                self.curr_comp=0

            self.curr_stt = 0
            self.curr_tts = None
            self.curr_llm = None
            self.curr_total = None

        if metric_entry:
            if not latency_metrics or latency_metrics[-1] != metric_entry:
                latency_metrics.append(metric_entry)
                self.user_state.extra_data["latency_metrics"] = latency_metrics




class UnpodTurnDetection(TurnTrackingObserver):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._is_user_speaking = False
        self._turn_end_timer = None
        self._pending_user_frames: Deque = deque()

    async def on_push_frame(self, data: FramePushed):
        """Process frame events for turn tracking.

        Args:
            data: Frame push event data containing the frame and metadata.
        """
        # Skip already processed frames
        if data.frame.id in self._processed_frames:
            return

        self._processed_frames.add(data.frame.id)
        self._frame_history.append(data.frame.id)

        # If we've exceeded our history size, remove the oldest frame ID
        # from the set of processed frames.
        if len(self._processed_frames) > len(self._frame_history):
            # Rebuild the set from the current deque contents
            self._processed_frames = set(self._frame_history)

        if isinstance(data.frame, StartFrame):
            # Start the first turn immediately when the pipeline starts
            if self._turn_count == 0:
                await self._start_turn(data)
        elif isinstance(data.frame, UserStartedSpeakingFrame):
            await self._handle_user_started_speaking(data)
        elif isinstance(data.frame, BotStartedSpeakingFrame):
            await self._handle_bot_started_speaking(data)
        # A BotStoppedSpeakingFrame can arrive after a UserStartedSpeakingFrame following an interruption
        # We only want to end the turn if the bot was previously speaking
        elif isinstance(data.frame, BotStoppedSpeakingFrame) and self._is_bot_speaking:
            await self._handle_bot_stopped_speaking(data)
        elif isinstance(data.frame, (EndFrame, CancelFrame)):
            await self._handle_pipeline_end(data)
        elif (
            isinstance(data.frame, UserStoppedSpeakingFrame) and self._is_user_speaking
        ):
            await self._handle_user_stopped_speaking(data)

    async def _handle_user_started_speaking(self, data: FramePushed):
        """Handle user speaking events, including interruptions."""
        self._is_user_speaking = True

        if self._is_bot_speaking:
            # Handle interruption - end current turn and start a new one
            self._cancel_turn_end_timer()  # Cancel any pending end turn timer
            await self._end_turn(data, was_interrupted=True)
            self._is_bot_speaking = False  # Bot is considered interrupted
            await self._start_turn(data)
        elif self._is_turn_active and self._has_bot_spoken:
            # User started speaking during the turn_end_timeout_secs period after bot speech
            self._cancel_turn_end_timer()  # Cancel any pending end turn timer
            await self._end_turn(data, was_interrupted=False)
            await self._start_turn(data)
        elif not self._is_turn_active:
            # Start a new turn after previous one ended
            await self._start_turn(data)
        else:
            # User is speaking within the same turn (before bot has responded)
            pass

    async def _handle_user_stopped_speaking(self, data: FramePushed):
        self._is_user_speaking = False
        print("user stopped speaking starting initial timeout for bot")

        if self._is_turn_active and not self._is_bot_speaking:
            self._bot_start_task = asyncio.create_task(self._bot_start_delay_task(data))
        else:
            print("No active turn or bot already speaking; no action needed.")

    async def _bot_start_delay_task(self, data: FramePushed):
        """Wait for configured delay; if user didn't resume speaking, finalize the user turn.

        This runs in a background Task; it must be cancellable when user restarts speaking.
        """
        try:
            await asyncio.sleep(1)
            print("await complete processing bot  frame ")
            if self._is_user_speaking:
                return
        except asyncio.CancelledError:
            return
