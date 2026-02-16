

from super.core.voice.base import BaseVoiceHandler
from typing import Optional,Any,Dict
from super.core.callback.base import BaseCallback
from super.core.configuration import BaseModelConfig
from super.core.voice.schema import  UserState
from livekit.agents import JobContext, MetricsCollectedEvent
from livekit.agents.voice import AgentSession
from super.core.voice.pipecat.services import ServiceFactory
from super.core.voice.services.livekit_services import (
    LiveKitServiceFactory
)
from super.core.voice.testing_agents.vanilla_agent import VanillaAgent

import asyncio

class VanillaAgenHandler(BaseVoiceHandler):
    def __init__(self,
        session_id: Optional[str] = None,
        user_state: Optional[UserState] = None,
        callback: Optional[BaseCallback] = None,
        model_config: Optional[BaseModelConfig] = None,
        observer: Optional[Any] = None ):

        super().__init__(
            session_id=session_id,
            callback=callback,
        )

        self.user_state = user_state
        self.config = model_config
        self.observer = observer
        self.session_id = session_id
        self.callback = callback
        self._services_initialized=False
        self._room_name =None
        self._job_context=None
        self._session=None
        self._agent = None
        self._service_factory=None


    @property
    def service_factory(self) -> LiveKitServiceFactory:
        """Lazy-initialized service factory."""
        if self._service_factory is None:
            self._service_factory = LiveKitServiceFactory(
                config=self.config,
                logger=self._logger.getChild("services"),
            )
        return self._service_factory



    async def preload_agent(
            self,
            user_state: UserState,
            observer: Optional[Any] = None,
    ) -> bool:
        try:
            self.user_state = user_state
            self.config = user_state.model_config or self.config
            self._room_name = user_state.room_name
            self.observer = observer
            self._services_initialized = True

            return True

        except Exception as e:
            self._logger.error(f"Preload failed: {e}")
            return False


    async def create_agent_session(
        self,
        ctx: JobContext,
        userdata: Optional[Dict[str, Any]] = None,
    ) -> AgentSession:

        return await self.service_factory.create_session(
            userdata=userdata, user_state=self.user_state
        )

    def set_event_bridge(self, event_bridge: Any) -> None:
        """Set LiveKit event bridge for compatibility with VoiceAgentHandler."""
        self._event_bridge = event_bridge

    async def execute(self, *args, **kwargs) -> Any:
        self._logger.warning(
            "VanillaAgenHandler execute() called without context. "
            "Use execute_with_context(ctx) for LiveKit native execution."
        )

    async def execute_with_context(self, ctx: "JobContext") -> Any:

        try:
            self._logger.info(
                f"Starting LiveKit session for {self.user_state.user_name}"
            )

            self._job_context = ctx

            session = await self.create_agent_session(ctx)
            self._session = session

            agent = self.create_agent(ctx)
            self._agent = agent

            self._setup_session_events(session)


            try:
                from livekit.agents.voice import room_io
                room_opts_kwargs={}
                room_options = room_io.RoomOptions(**room_opts_kwargs)

                await self._session.start(
                    room=ctx.room,
                    agent=agent,
                    room_options=room_options,
                )

                await ctx.connect()
                self._logger.info("Connected to room")

            except Exception as e:
                self._logger.error(f"Failed to start LiveKit session: {e}")
                import traceback
                self._logger.error(traceback.format_exc())
                raise

        except Exception as e:
            self._logger.error(f"LiveKit session error: {e}")
            import traceback
            self._logger.error(traceback.format_exc())
            raise



    def _setup_session_events(self, session: AgentSession) -> None:

        @session.on("metrics_collected")
        def on_metrics(event: MetricsCollectedEvent):
            asyncio.create_task(_handle_metrics(event))


        async def _handle_metrics(event: MetricsCollectedEvent):
            """Handle metrics collection."""
            await handle_metrics(event)

        llm_met = None
        tts_met = None
        eou_met = None
        stt_met = None
        turn_count = 0
        cumulative_stt = 0.0
        cumulative_llm = 0.0
        cumulative_tts = 0.0
        cumulative_total = 0
        real_time_model_met = 0
        realtime_total = 0
        completion_tokens = 0
        prompt_tokens = 0

        async def handle_metrics(ev):
            from livekit.agents import metrics

            nonlocal llm_met, tts_met, eou_met

            nonlocal turn_count, cumulative_stt, cumulative_llm, cumulative_tts, cumulative_total, stt_met, real_time_model_met, realtime_total, prompt_tokens, completion_tokens

            metrics.log_metrics(ev.metrics)

            if type(ev.metrics) == metrics.EOUMetrics:
                eou_met = ev.metrics
            elif type(ev.metrics) == metrics.LLMMetrics:
                llm_met = ev.metrics
                completion_tokens = llm_met.completion_tokens
                prompt_tokens = llm_met.prompt_tokens
            elif type(ev.metrics) == metrics.TTSMetrics:
                tts_met = ev.metrics
            elif type(ev.metrics) == metrics.STTMetrics:
                stt_met = ev.metrics
            elif type(ev.metrics) == metrics.RealtimeModelMetrics:
                if ev.metrics.ttft > 0:
                    real_time_model_met = ev.metrics.ttft
                    print(f"\n\n Realtime : {ev.metrics} \n\n ")

            if real_time_model_met:
                turn_count += 1
                realtime_total += real_time_model_met

                latency_data = self.user_state.extra_data.get("latency_metrics", [])
                latency_data.append({"realtime_latency": real_time_model_met, "realtime_avg": realtime_total / turn_count})
                print(
                    f"\n\n real_time_model_met avg : {realtime_total / turn_count} \n\n "
                )

                real_time_model_met = None

            if eou_met and llm_met and tts_met:
                stt_latency = eou_met.end_of_utterance_delay
                llm_latency = llm_met.ttft
                tts_latency = tts_met.ttfb

                current_turn_total = stt_latency + llm_latency + tts_latency

                turn_count += 1
                cumulative_stt += stt_latency
                cumulative_llm += llm_latency
                cumulative_tts += tts_latency
                cumulative_total += current_turn_total

                avg_stt = cumulative_stt / turn_count
                avg_llm = cumulative_llm / turn_count
                avg_tts = cumulative_tts / turn_count
                avg__current_total = cumulative_total / turn_count
                # avg_total = (avg_stt + avg_llm + avg_tts)/turn_count

                add_latency_chart(turn_count, llm_latency, tts_latency, stt_latency, current_turn_total, avg_llm,
                                       avg_stt, avg_tts, avg__current_total, prompt_tokens, completion_tokens)

                print(f"\n{'=' * 60}")
                print(f"Turn #{turn_count} Metrics:")
                # print(f"  Current - STT: {stt_latency:.2f}ms | LLM: {llm_latency:.2f}ms | TTS: {tts_latency:.2f}ms")
                # print(f"  Current Turn Total (avg): {current_turn_total:.2f}ms")
                print(f"\nRunning Averages (across all {turn_count} turns):")
                print(
                    f"Avg STT: {avg_stt:.2f}s | Avg LLM: {avg_llm:.2f}s | Avg TTS: {avg_tts:.2f}s"
                )
                print(f"\n Avg of current total{avg__current_total:.2f} s")
                # print(f"  Overall Avg Total: {avg_total:.2f}s")
                print(f"{'=' * 60}\n")

                eou_met = None
                llm_met = None
                tts_met = None
                stt_met = None
                prompt_tokens = 0
                completion_tokens = 0

        def add_latency_chart(turn_count, llm_latency, tts_latency, stt_latency, current_turn_total, avg_llm, avg_stt,
                              avg_tts, avg__current_total, prompt_tokens, completion_tokens):
            if not isinstance(self.user_state.extra_data, dict):
                self.user_state.extra_data = {}

            latency_data = self.user_state.extra_data.get("latency_metrics", [])
            provider_data = self.user_state.extra_data.get("service_modes")

            latency_entry = {
                "turn_count": turn_count,
                "llm_latency": llm_latency,
                "tts_latency": tts_latency,
                "stt_latency": stt_latency,
                "total_latency": current_turn_total,
                "avg_llm_latency": avg_llm,
                "avg_stt_latency": avg_stt,
                "avg_tts_latency": avg_tts,
                "avg_total_latency": avg__current_total,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
            }

            if provider_data:
                try:
                    latency_entry['stt_provider'] = provider_data.stt_provider
                    latency_entry['tts_provider'] = provider_data.tts_provider
                    latency_entry['llm_provider'] = provider_data.llm_provider
                    latency_entry['llm_type'] = provider_data.llm_type
                    latency_entry['stt_type'] = provider_data.stt_type
                    latency_entry['tts_type'] = provider_data.tts_type

                except Exception as e:
                    pass

            latency_data.append(latency_entry)

            self.user_state.extra_data["latency_metrics"] = latency_data


    def create_agent(self, ctx) -> "Agent":
        """Create the LiveKit agent (state built internally by agent)."""
        instructions = self.config.get("system_prompt")

        agent = VanillaAgent(
            handler=self,
            user_state=self.user_state,
            instructions=instructions,
            ctx=ctx,
            config=self.config,
        )

        return agent


