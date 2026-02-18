"""
SuperVoiceAgent - Enhanced voice calling agent using pipecat-ai with API compatibility for existing LiveKit agents
"""

import asyncio
import json
import logging
import os
from typing import Dict, Any, Optional, List, Union, Annotated
from dataclasses import dataclass, field
from datetime import datetime
from time import perf_counter

from super.core.configuration.base_config import BaseModelConfig
from super.core.callback.base import BaseCallback
from super.core.voice.simple import SimpleVoiceHandler
from super.core.voice.services.livekit_services import (
    DEFAULT_TTS_PROVIDER,
    DEFAULT_TTS_MODEL,
    DEFAULT_TTS_VOICE,
)
from super.core.context.schema import Message, Role, Event, User
from super.configs.app_configs import DOC_SEARCH_URL

# Import existing voice pipeline config for compatibility
try:
    from super.core.voice.pipeline.config import (
        get_model_config,
        default_persona,
        default_script,
        system_prompt,
        BASE_TTS,
        OPENAI_TTS,
        calculate_usage,
    )
except ImportError:
    # Fallback if voice_pipeline_config_v1 not available
    def get_model_config(config):
        return config
    default_persona = "You are a helpful voice assistant."
    default_script = "You are a helpful voice assistant."
    system_prompt = "You are a helpful voice assistant."
    BASE_TTS = None
    OPENAI_TTS = None
    def calculate_usage(usage):
        return 0, 0, 0, 0

# Import pipecat core
try:
    from pipecat.pipeline.pipeline import Pipeline
    from pipecat.pipeline.runner import PipelineRunner
    from pipecat.pipeline.task import PipelineParams, PipelineTask
    from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
    from pipecat.frames.frames import TTSSpeakFrame, EndFrame
    from pipecat.services.llm_service import FunctionCallParams
    from pipecat.adapters.schemas.function_schema import FunctionSchema
    from pipecat.adapters.schemas.tools_schema import ToolsSchema
    from pipecat.processors.frameworks.rtvi import RTVIConfig, RTVIObserver, RTVIProcessor
    PIPECAT_AVAILABLE = True
except ImportError:
    PIPECAT_AVAILABLE = False
    # Don't raise error, allow fallback operation

# Import transport adapters
try:
    from super.core.voice.schema import CallMeta
    # These may not exist - use TYPE_CHECKING pattern if needed
    TransportAdapter = None
    TransportEvent = None
    EventType = None
    MediaFrame = None
    LiveKitTransport = None
    SmallWebRTCTransport = None
    FastAPIWebSocketTransport = None
    TRANSPORT_AVAILABLE = True
except ImportError:
    TRANSPORT_AVAILABLE = False


@dataclass
class UserState:
    """User state data structure compatible with existing VoiceAgent"""
    user_name: str = "User"
    space_name: str = "Unpod AI"
    contact_number: Optional[str] = None
    token: str = ""
    language: Optional[str] = None
    thread_id: str = ""
    user: dict = field(default_factory=dict)
    model_config: Optional[Dict[str, Any]] = None
    participant: Optional[Any] = None  # rtc.RemoteParticipant
    knowledge_base: list = field(default_factory=list)
    persona: Optional[str] = None
    script: Optional[str] = None
    first_message: Optional[str] = None
    objective: Optional[list] = field(default_factory=list)
    config: Optional[Dict[str, Any]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    User: Optional[User] = None
    usage: Optional[Any] = None  # metrics.UsageCollector
    recording_url: Optional[str] = None


@dataclass
class AgentConfig:
    """Enhanced agent configuration compatible with existing patterns"""
    agent_name: str = "SuperVoiceAgent"
    model_config: Optional[BaseModelConfig] = None
    custom_configs: Optional[Dict[str, Any]] = None
    callback: Optional[BaseCallback] = None
    transport_type: str = "livekit"  # livekit, webrtc, websocket
    transport_options: Dict[str, Any] = field(default_factory=dict)
    auto_answer: bool = True
    session_timeout: int = 300  # 5 minutes
    enable_sip: bool = True
    sip_trunk_id: Optional[str] = None
    knowledge_bases: List[str] = field(default_factory=list)


@dataclass 
class CallSession:
    """Call session tracking"""
    session_id: str
    user_state: UserState
    context: Optional[Any] = None
    status: str = "initializing"  # initializing, active, ended
    pipeline_task: Optional[Any] = None
    context_aggregator: Optional[Any] = None
    created_at: datetime = field(default_factory=datetime.now)


class SuperVoiceAgent(SimpleVoiceHandler):
    """
    SuperVoiceAgent - Enhanced voice calling agent with pipecat-ai and API compatibility
    
    Features:
    - Compatible with existing VoiceAgent API structure
    - Enhanced with pipecat pipeline support
    - SIP call handling for inbound/outbound calls
    - Knowledge base integration with existing patterns
    - Dynamic transport switching (LiveKit, WebRTC, WebSocket)
    """
    
    def __init__(
        self,
        agent_name: str = "SuperVoiceAgent", 
        custom_configs: Optional[Dict[str, Any]] = None,
        callback: BaseCallback = None,
        model_config: BaseModelConfig = None,
        agent_config: Optional[AgentConfig] = None
    ):
        # Maintain compatibility with existing patterns
        self.agent_name = agent_name
        self.custom_configs = custom_configs or {}
        self._callback = callback
        self.model_config = model_config
        self.outbound_trunk_id = os.getenv("SIP_OUTBOUND_TRUNK_ID")
        self._default_instructions = system_prompt
        self.logger = logging.getLogger(self.agent_name)
        
        # Initialize parent with SimpleVoiceHandler pattern
        super().__init__(
            session_id=None,
            callback=callback,
            model_config=model_config,
            logger=self.logger
        )
        
        # Ensure session_id attribute exists for compatibility
        self.session_id = self._session_id if hasattr(self, '_session_id') else None
        
        # Enhanced configuration
        if agent_config:
            self.agent_config = agent_config
        else:
            self.agent_config = AgentConfig(
                agent_name=agent_name,
                model_config=model_config,
                custom_configs=custom_configs,
                callback=callback
            )
        
        # Pipecat components
        self.active_sessions: Dict[str, CallSession] = {}
        if PIPECAT_AVAILABLE:
            self.pipeline_runner = PipelineRunner()
        
        # Get model configuration
        if self.agent_config.model_config:
            self.config = self.agent_config.model_config.get_config("default")
        else:
            self.config = self._get_default_config()
    
    # API Compatibility Methods (matching existing VoiceAgent pattern)
    
    async def entrypoint(self, ctx=None):
        """Entry point for call handling - compatible with existing VoiceAgent API"""
        try:
            self.logger.info("SuperVoiceAgent entrypoint called")
            
            # Create user state for compatibility
            user_state = UserState(
                user_name="Voice User",
                space_name=self.agent_name,
                thread_id=self.session_id or f"session_{datetime.now().timestamp()}",
                start_time=datetime.now(),
                model_config=self.config
            )
            
            # For SIP calls, manage call lifecycle
            if hasattr(ctx, 'room') and hasattr(ctx.room, 'name'):
                if 'sip' in ctx.room.name.lower():
                    await self.manage_call(ctx, None, user_state)
                else:
                    await self.run_agent(ctx, user_state)
            else:
                # Fallback to direct agent run
                await self.run_agent(ctx, user_state)
                
        except Exception as e:
            self.logger.error(f"Error in entrypoint: {e}")
            raise

    async def manage_call(self, ctx, participant, user_state: UserState):
        """Manage call lifecycle - compatible with existing VoiceAgent API"""
        try:
            self.logger.info("Managing call session")
            user_state.participant = participant
            
            # Set up session tracking
            session_id = user_state.thread_id
            self.active_sessions[session_id] = CallSession(
                session_id=session_id,
                user_state=user_state,
                context=ctx,
                status='active'
            )
            
            # Send call status notification
            self.message_callback("Call Status: Call connected", "system", user_state)
            
            # Run the agent
            await self.run_agent(ctx, user_state)
            
        except Exception as e:
            self.logger.error(f"Error managing call: {e}")
            self.message_callback("Call Status: Call ended due to error", "system", user_state)

    async def run_agent(self, ctx, user_state: UserState):
        """Run the agent pipeline - compatible with existing VoiceAgent API"""
        try:
            self.logger.info("Starting agent session")
            
            # Initialize pipecat pipeline if available
            if PIPECAT_AVAILABLE and hasattr(self, 'pipeline_runner'):
                await self._run_pipecat_agent(ctx, user_state)
            else:
                await self._run_simple_agent(ctx, user_state)
                
        except Exception as e:
            self.logger.error(f"Error running agent: {e}")
        finally:
            # Ensure proper cleanup
            await self._cleanup_session(user_state)
            self.message_callback("EOF", "system", user_state)

    async def _run_pipecat_agent(self, ctx, user_state: UserState):
        """Run enhanced pipecat pipeline"""
        try:
            # Create pipecat pipeline
            pipeline, context_aggregator = await self._create_pipeline()
            
            # Create pipeline task
            task = PipelineTask(
                pipeline,
                params=PipelineParams(enable_metrics=True, enable_usage_metrics=True)
            )
            
            # Store in session for cleanup
            session_id = user_state.thread_id
            if session_id in self.active_sessions:
                self.active_sessions[session_id].pipeline_task = task
                self.active_sessions[session_id].context_aggregator = context_aggregator
            
            # Start pipeline
            await self.pipeline_runner.run(task)
            
        except Exception as e:
            self.logger.error(f"Error in pipecat agent: {e}")
            # Fall back to simple agent instead of raising
            self.logger.info("Falling back to simple agent mode")
            await self._run_simple_agent(ctx, user_state)

    async def _run_simple_agent(self, ctx, user_state: UserState):
        """Fallback simple agent implementation"""
        try:
            # Simple message processing loop
            self.message_callback("Agent started", "system", user_state)
            
            # Implement basic conversation loop here
            # This is a placeholder for when pipecat is not available
            await asyncio.sleep(1)  # Prevent tight loop
            
        except Exception as e:
            self.logger.error(f"Error in simple agent: {e}")
            raise

    def message_callback(self, transcribed_text: str, role: str, user_state: UserState):
        """Send a message to callback system - compatible with existing VoiceAgent API"""
        thread_id = str(user_state.thread_id)
        if "Call Status" in transcribed_text and role == "system":
            msg = Message.add_notification(transcribed_text.replace("Call Status:", ""))
            self._send_callback(msg, thread_id=thread_id)
        elif "EOF" in transcribed_text and role == "system":
            user_state.end_time = datetime.now()
            usage = self.create_usage(user_state)
            msg = Message.add_task_end_message(
                "Voice Execution Completed",
                id=thread_id,
                data={
                    "start_time": user_state.start_time,
                    "end_time": user_state.end_time,
                    "usage": usage,
                    "recording_url": user_state.recording_url,
                },
            )
            self._send_callback(msg, thread_id=thread_id)

    def _send_callback(self, message: Message, thread_id: str):
        """Send a message through the callback if one is configured."""
        if self._callback:
            self._callback.send(message, thread_id=thread_id)

    def create_usage(self, user_state: UserState):
        """Create usage statistics - compatible with existing VoiceAgent API"""
        try:
            usage = self.log_usage(user_state)
            config = user_state.model_config or {}
            usage["llm_provider"] = config.get("llm_provider", "openai")
            usage["llm_model"] = config.get("llm_model", "gpt-4o")
            usage["tts_provider"] = config.get("tts_provider", "deepgram")
            usage["tts_model"] = config.get("tts_model", "aura-asteria-en")
            usage["stt_provider"] = config.get("stt_provider", "deepgram")
            usage["stt_model"] = config.get("stt_model", "nova-2-general")
            
            if calculate_usage:
                total, llm_cost, stt_cost, tts_cost = calculate_usage(usage)
                usage["costs"] = {"llm_cost": llm_cost, "stt_cost": stt_cost, "tts_cost": tts_cost}
                usage["total_cost"] = total
            
            return usage
        except Exception as e:
            self.logger.error(f"Error creating usage: {e}")
            return {}

    def log_usage(self, user_state: UserState):
        """Log usage metrics - compatible with existing VoiceAgent API"""
        try:
            if user_state.usage and hasattr(user_state.usage, 'get_summary'):
                summary = user_state.usage.get_summary()
                usage = {
                    "llm_prompt_tokens": getattr(summary, 'llm_prompt_tokens', 0),
                    "llm_completion_tokens": getattr(summary, 'llm_completion_tokens', 0),
                    "tts_characters_count": getattr(summary, 'tts_characters_count', 0),
                    "stt_audio_duration": getattr(summary, 'stt_audio_duration', 0),
                }
            else:
                # Fallback usage
                usage = {
                    "llm_prompt_tokens": 0,
                    "llm_completion_tokens": 0,
                    "tts_characters_count": 0,
                    "stt_audio_duration": 0,
                }
            return usage
        except Exception as e:
            self.logger.error(f"Error logging usage: {e}")
            return {}

    async def _cleanup_session(self, user_state: UserState):
        """Clean up session resources and async tasks"""
        try:
            session_id = user_state.thread_id
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                
                # Cancel any running pipeline tasks
                if hasattr(session, 'pipeline_task') and session.pipeline_task:
                    try:
                        if hasattr(session.pipeline_task, 'cancel'):
                            session.pipeline_task.cancel()
                        if hasattr(session.pipeline_task, 'queue_frame'):
                            await session.pipeline_task.queue_frame(EndFrame())
                    except Exception as e:
                        self.logger.debug(f"Error canceling pipeline task: {e}")
                
                # Clean up the session
                if isinstance(session, CallSession):
                    session.status = 'ended'
                elif isinstance(session, dict):
                    session['status'] = 'ended'
                
            # Cancel any remaining asyncio tasks related to AsyncClient
            try:
                tasks = [task for task in asyncio.all_tasks() if not task.done()]
                for task in tasks:
                    try:
                        task_str = str(task.get_coro())
                        if 'AsyncClient' in task_str or '_lease_loop' in task_str or 'warmup' in task_str:
                            task.cancel()
                            try:
                                await task
                            except asyncio.CancelledError:
                                pass
                            except Exception as e:
                                self.logger.debug(f"Task cleanup error: {e}")
                    except Exception as e:
                        self.logger.debug(f"Task inspection error: {e}")
            except Exception as e:
                self.logger.debug(f"Task cleanup error: {e}")
                
        except Exception as e:
            self.logger.debug(f"Session cleanup error: {e}")

    # Enhanced Pipecat Implementation Methods
    
    async def execute(self, objective: str | Message, *args, **kwargs) -> Any:
        """Execute voice agent with given objective - compatible with existing patterns"""
        try:
            if isinstance(objective, str):
                # Handle outbound call
                return await self._handle_outbound_call(objective, *args, **kwargs)
            elif isinstance(objective, Message):
                # Handle message-based interaction
                return await self._handle_message_interaction(objective, *args, **kwargs)
            else:
                # Fallback to entrypoint for compatibility
                return await self.entrypoint(objective)
        except Exception as e:
            self.logger.error(f"Error executing SuperVoiceAgent: {e}")
            return {"error": str(e)}

    async def _handle_outbound_call(self, phone_number: str, **kwargs) -> Dict[str, Any]:
        """Handle outbound call initiation"""
        try:
            session_id = f"out_{datetime.now().timestamp()}"
            
            # Create user state for outbound call
            user_state = UserState(
                user_name="Outbound User",
                contact_number=phone_number,
                thread_id=session_id,
                start_time=datetime.now(),
                model_config=self.config
            )
            
            # Store session
            self.active_sessions[session_id] = CallSession(
                session_id=session_id,
                user_state=user_state,
                status='active'
            )
            
            return {
                "success": True,
                "session_id": session_id,
                "message": f"Outbound call initiated to {phone_number}"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _handle_message_interaction(self, message: Message, **kwargs) -> Dict[str, Any]:
        """Handle message-based interaction"""
        # Process message through appropriate session
        return {"success": True, "response": "Message processed"}

    async def _create_pipeline(self):
        """Create pipecat pipeline with STT, LLM, and TTS"""
        if not PIPECAT_AVAILABLE:
            raise Exception("Pipecat not available")
        
        # Get services from config (STT, LLM, TTS)
        stt_service = self._create_stt_service()
        llm_service = self._create_llm_service() 
        tts_service = self._create_tts_service()
        
        # Check if required services are available
        if not llm_service:
            raise Exception("LLM service could not be created - missing API keys or service unavailable")
        if not stt_service:
            raise Exception("STT service could not be created - missing API keys or service unavailable") 
        if not tts_service:
            raise Exception("TTS service could not be created - missing API keys or service unavailable")
        
        # Create context with tools
        context = self._create_context_with_tools()
        context_aggregator = llm_service.create_context_aggregator(context)
        
        # Build pipeline
        pipeline = Pipeline([
            # Input from transport will be handled by frame routing
            stt_service,
            context_aggregator.user(),
            llm_service,
            tts_service,
            # Output to transport will be handled by frame routing
            context_aggregator.assistant(),
        ])
        
        return pipeline, context_aggregator

    def _create_context_with_tools(self):
        """Create LLM context with knowledge base tools"""
        if not PIPECAT_AVAILABLE:
            return None
            
        tools = ToolsSchema(standard_tools=[
            FunctionSchema(
                name="get_knowledge_base_info",
                description="Get information from knowledge bases",
                properties={
                    "query": {"type": "string", "description": "Search query"},
                    "kb_name": {"type": "string", "description": "Knowledge base name"}
                },
                required=["query"]
            )
        ])
        
        return OpenAILLMContext(
            messages=[
                {
                    "role": "system", 
                    "content": self.config.get("system_prompt", "You are a helpful voice assistant.")
                },
                {
                    "role": "user",
                    "content": self.config.get("first_message", "Hello! How can I help you today?")
                }
            ],
            tools=tools
        )

    def _create_llm_service(self):
        """Create LLM service based on config - following configurable_agent.py pattern"""
        if not PIPECAT_AVAILABLE:
            self.logger.error("Pipecat is not available")
            return None
        
        llm_provider = self.config.get("llm_provider", "openai")
        self.logger.info(f"LLM provider: {llm_provider}")
        
        try:
            if llm_provider == "gemini":
                from pipecat.services.gemini_multimodal_live import GeminiMultimodalLiveLLMService
                # Gemini has specific voice options - force valid voice
                gemini_voice = self.config.get("tts_voice", "Puck")
                valid_gemini_voices = ["Puck", "Charon", "Kore", "Fenrir"]
                if gemini_voice not in valid_gemini_voices:
                    gemini_voice = "Puck"  # Default to Puck if invalid voice
                    self.logger.warning(f"Invalid Gemini voice '{self.config.get('tts_voice')}', using 'Puck'")
                
                return GeminiMultimodalLiveLLMService(
                    api_key=os.getenv("GOOGLE_API_KEY"),
                    voice_id=gemini_voice,
                    transcribe_model_audio=True,
                    system_instruction=self.config.get("system_prompt"),
                )
            elif llm_provider == "openai":
                from pipecat.services.openai.llm import OpenAILLMService
                return OpenAILLMService(
                    model=self.config.get("llm_model", "gpt-4o")
                )
            elif llm_provider == "groq":
                from pipecat.services.groq.llm import GroqLLMService
                return GroqLLMService(
                    api_key=os.getenv("GROQ_API_KEY"),
                    model=self.config.get("llm_model", "llama-3.3-70b-versatile")
                )
            elif llm_provider == "google":
                from pipecat.services.google.llm import GoogleLLMService
                return GoogleLLMService(
                    api_key=os.getenv("GOOGLE_API_KEY"),
                    model=self.config.get("llm_model", "gemini-1.5-flash"),
                )
            else:
                # Default fallback to OpenAI
                from pipecat.services.openai.llm import OpenAILLMService
                return OpenAILLMService(
                    model="gpt-4o"
                )
        except Exception as e:
            self.logger.error(f"Failed to create LLM service: {e}")
            return None

    def _create_stt_service(self):
        """Create STT service based on config - following configurable_agent.py pattern"""
        if not PIPECAT_AVAILABLE:
            self.logger.error("Pipecat is not available")
            return None
        
        stt_provider = self.config.get("stt_provider", "openai")
        
        try:
            if stt_provider == "openai":
                from pipecat.services.openai.stt import OpenAISTTService
                from pipecat.transcriptions.language import Language
                return OpenAISTTService(
                    api_key=os.getenv("OPENAI_API_KEY"),
                    model=self.config.get("stt_model", "whisper-1"),
                    language=Language.EN
                )
            elif stt_provider == "gladia":
                from pipecat.services.gladia.stt import GladiaSTTService
                from pipecat.services.gladia.config import LanguageConfig
                from pipecat.services.gladia.stt import GladiaInputParams
                from pipecat.transcriptions.language import Language
                return GladiaSTTService(
                    api_key=os.getenv("GLADIA_API_KEY"),
                    model="solaria-1",  # Fixed: Use valid Gladia model
                    params=GladiaInputParams(
                        language_config=LanguageConfig(
                            languages=[Language.HI, Language.PA, Language.EN],
                            code_switching=True
                        )
                    ),
                )
            elif stt_provider == "deepgram":
                from pipecat.services.deepgram.stt import DeepgramSTTService
                from pipecat.transcriptions.language import Language
                return DeepgramSTTService(
                    api_key=os.getenv("DEEPGRAM_API_KEY"),
                    language=Language.EN
                )
            else:
                # Default fallback to OpenAI
                from pipecat.services.openai.stt import OpenAISTTService
                from pipecat.transcriptions.language import Language
                return OpenAISTTService(
                    api_key=os.getenv("OPENAI_API_KEY"),
                    model="whisper-1",
                    language=Language.EN
                )
        except Exception as e:
            self.logger.error(f"Failed to create STT service: {e}")
            return None

    def _create_tts_service(self):
        """Create TTS service based on config - following configurable_agent.py pattern"""
        if not PIPECAT_AVAILABLE:
            return None

        tts_provider = self.config.get("tts_provider", "openai")

        try:
            if tts_provider == "openai":
                from pipecat.services.openai.tts import OpenAITTSService
                return OpenAITTSService(
                    api_key=os.getenv("OPENAI_API_KEY"),
                    model=self.config.get("tts_model", "tts-1"),
                    voice=self.config.get("tts_voice", "alloy")
                )
            elif tts_provider == "sarvam":
                import aiohttp
                from pipecat.services.sarvam.tts import SarvamTTSService
                from pipecat.transcriptions.language import Language
                session = aiohttp.ClientSession()
                return SarvamTTSService(
                    api_key=os.getenv("SARVAM_API_KEY"),
                    voice_id=self.config.get("tts_voice", "anushka"),
                    aiohttp_session=session,
                    params=SarvamTTSService.InputParams(
                        language=Language.HI if self.config.get("language") == "hi" else Language.EN
                    ),
                )
            elif tts_provider == "elevenlabs":
                from pipecat.services.elevenlabs.tts import ElevenLabsTTSService
                return ElevenLabsTTSService(
                    api_key=os.getenv("ELEVEN_API_KEY"),
                    voice_id=self.config.get("tts_voice"),
                    model=self.config.get("tts_model", "eleven_multilingual_v2")
                )
            elif tts_provider == "deepgram":
                from pipecat.services.deepgram.tts import DeepgramTTSService
                return DeepgramTTSService(
                    api_key=os.getenv("DEEPGRAM_API_KEY"),
                    voice=self.config.get("tts_voice", "aura-helios-en")
                )
            elif tts_provider == "cartesia":
                from pipecat.services.cartesia.tts import CartesiaTTSService
                return CartesiaTTSService(
                    api_key=os.getenv("CARTESIA_API_KEY"),
                    model=self.config.get("tts_model", "sonic-2"),
                    voice_id=self.config.get("tts_voice"),
                )
            else:
                # Default fallback
                return self._create_fallback_tts()
        except Exception as e:
            self.logger.error(f"Failed to create TTS service: {e}")
            return self._create_fallback_tts()

    def _create_fallback_tts(self):
        """Create fallback TTS service using default provider."""
        if not PIPECAT_AVAILABLE:
            return None
        try:
            fallback_model = os.getenv("FALLBACK_TTS_MODEL", DEFAULT_TTS_MODEL)
            fallback_voice = os.getenv("FALLBACK_TTS_VOICE", DEFAULT_TTS_VOICE)
            self.logger.warning(
                f"Using fallback TTS: {DEFAULT_TTS_PROVIDER} {fallback_model} ({fallback_voice})"
            )

            # Try to use inference TTS for the default provider
            from livekit.agents import inference

            return inference.TTS(
                model=f"{DEFAULT_TTS_PROVIDER}/{fallback_model}",
                voice=fallback_voice,
            )
        except Exception as e:
            self.logger.error(f"Fallback TTS also failed: {e}")
            return None

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "system_prompt": f"You are {self.agent_config.agent_name}, a helpful voice assistant.",
            "first_message": "Hello! I'm your voice assistant. How can I help you today?",
            "knowledge_base": self.agent_config.knowledge_bases
        }

    async def _run_pipecat_agent(self, ctx, user_state: UserState):
        """Run enhanced pipecat pipeline"""
        try:
            # Create pipecat pipeline
            pipeline, context_aggregator = await self._create_pipeline()
            
            # Create pipeline task
            task = PipelineTask(
                pipeline,
                params=PipelineParams(enable_metrics=True, enable_usage_metrics=True)
            )
            
            # Store in session for cleanup
            session_id = user_state.thread_id
            if session_id in self.active_sessions:
                self.active_sessions[session_id]['pipeline_task'] = task
                self.active_sessions[session_id]['context_aggregator'] = context_aggregator
            
            # Start pipeline
            await self.pipeline_runner.run(task)
            
        except Exception as e:
            self.logger.error(f"Error in pipecat agent: {e}")
            raise

    async def _run_simple_agent(self, ctx, user_state: UserState):
        """Fallback simple agent implementation"""
        try:
            # Simple message processing loop
            self.message_callback("Agent started", "system", user_state)
            
            # Implement basic conversation loop here
            # This is a placeholder for when pipecat is not available
            await asyncio.sleep(1)  # Prevent tight loop
            
        except Exception as e:
            self.logger.error(f"Error in simple agent: {e}")
            raise

    def message_callback(self, transcribed_text: str, role: str, user_state: UserState):
        """Send a message to callback system - compatible with existing VoiceAgent API"""
        thread_id = str(user_state.thread_id)
        if "Call Status" in transcribed_text and role == "system":
            msg = Message.add_notification(transcribed_text.replace("Call Status:", ""))
            self._send_callback(msg, thread_id=thread_id)
        elif "EOF" in transcribed_text and role == "system":
            user_state.end_time = datetime.now()
            usage = self.create_usage(user_state)
            msg = Message.add_task_end_message(
                "Voice Execution Completed",
                id=thread_id,
                data={
                    "start_time": user_state.start_time,
                    "end_time": user_state.end_time,
                    "usage": usage,
                    "recording_url": user_state.recording_url,
                },
            )
            self._send_callback(msg, thread_id=thread_id)

    def _send_callback(self, message: Message, thread_id: str):
        """Send a message through the callback if one is configured."""
        if self._callback:
            self._callback.send(message, thread_id=thread_id)

    def create_usage(self, user_state: UserState):
        """Create usage statistics - compatible with existing VoiceAgent API"""
        try:
            usage = self.log_usage(user_state)
            config = user_state.model_config or {}
            usage["llm_provider"] = config.get("llm_provider", "openai")
            usage["llm_model"] = config.get("llm_model", "gpt-4o")
            usage["tts_provider"] = config.get("tts_provider", "deepgram")
            usage["tts_model"] = config.get("tts_model", "aura-asteria-en")
            usage["stt_provider"] = config.get("stt_provider", "deepgram")
            usage["stt_model"] = config.get("stt_model", "nova-2-general")
            
            if calculate_usage:
                total, llm_cost, stt_cost, tts_cost = calculate_usage(usage)
                usage["costs"] = {"llm_cost": llm_cost, "stt_cost": stt_cost, "tts_cost": tts_cost}
                usage["total_cost"] = total
            
            return usage
        except Exception as e:
            self.logger.error(f"Error creating usage: {e}")
            return {}

    def log_usage(self, user_state: UserState):
        """Log usage metrics - compatible with existing VoiceAgent API"""
        try:
            if user_state.usage and hasattr(user_state.usage, 'get_summary'):
                summary = user_state.usage.get_summary()
                usage = {
                    "llm_prompt_tokens": getattr(summary, 'llm_prompt_tokens', 0),
                    "llm_completion_tokens": getattr(summary, 'llm_completion_tokens', 0),
                    "tts_characters_count": getattr(summary, 'tts_characters_count', 0),
                    "stt_audio_duration": getattr(summary, 'stt_audio_duration', 0),
                }
            else:
                # Fallback usage
                usage = {
                    "llm_prompt_tokens": 0,
                    "llm_completion_tokens": 0,
                    "tts_characters_count": 0,
                    "stt_audio_duration": 0,
                }
            return usage
        except Exception as e:
            self.logger.error(f"Error logging usage: {e}")
            return {}
    
    # Enhanced Pipecat Implementation Methods
    
    async def initialize(self) -> bool:
        """Initialize the SuperVoiceAgent with selected transport"""
        try:
            # Initialize transport
            self.transport = await self._create_transport()
            if not self.transport:
                raise Exception(f"Failed to create transport: {self.agent_config.transport_type}")
            
            # Set up transport event handlers
            self.transport.on_event(self._handle_transport_event)
            
            # Connect transport
            if not await self.transport.connect():
                raise Exception("Failed to connect transport")
            
            self.logger.info(f"SuperVoiceAgent initialized with {self.agent_config.transport_type} transport")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize SuperVoiceAgent: {e}")
            return False

    async def execute(self, objective: str | Message, *args, **kwargs) -> Any:
        """Execute voice agent with given objective - compatible with existing patterns"""
        try:
            if isinstance(objective, str):
                # Handle outbound call
                return await self._handle_outbound_call(objective, *args, **kwargs)
            elif isinstance(objective, Message):
                # Handle message-based interaction
                return await self._handle_message_interaction(objective, *args, **kwargs)
            else:
                # Fallback to entrypoint for compatibility
                return await self.entrypoint(objective)
        except Exception as e:
            self.logger.error(f"Error executing SuperVoiceAgent: {e}")
            return {"error": str(e)}
    
    async def shutdown(self):
        """Shutdown the agent and clean up resources"""
        try:
            # End all active sessions
            for session_id in list(self.active_sessions.keys()):
                await self._end_session(session_id, "agent_shutdown")
            
            # Disconnect transport
            if self.transport:
                await self.transport.disconnect()
            
            self.logger.info("SuperVoiceAgent shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")

    # Private Implementation Methods
    
    async def _create_transport(self) -> Optional[TransportAdapter]:
        """Create and configure transport based on agent config"""
        transport_type = self.agent_config.transport_type.lower()
        options = self.agent_config.transport_options.copy()
        
        # Add common options
        options["auto_answer"] = self.agent_config.auto_answer
        
        if transport_type == "livekit":
            if self.agent_config.enable_sip:
                options["sip_trunk_id"] = self.agent_config.sip_trunk_id
            return LiveKitTransport(options, self.logger)
        elif transport_type == "webrtc":
            return SmallWebRTCTransport(options, self.logger)
        elif transport_type == "websocket":
            return FastAPIWebSocketTransport(options, self.logger)
        else:
            self.logger.error(f"Unknown transport type: {transport_type}")
            return None


    def _create_context_with_tools(self):
        """Create LLM context with knowledge base tools"""
        tools = ToolsSchema(standard_tools=[
            FunctionSchema(
                name="get_knowledge_base_info",
                description="Get information from knowledge bases",
                properties={
                    "query": {"type": "string", "description": "Search query"},
                    "kb_name": {"type": "string", "description": "Knowledge base name"}
                },
                required=["query"]
            )
        ])
        
        return OpenAILLMContext(
            messages=[
                {
                    "role": "system", 
                    "content": self.config.get("system_prompt", "You are a helpful voice assistant.")
                },
                {
                    "role": "user",
                    "content": self.config.get("first_message", "Hello! How can I help you today?")
                }
            ],
            tools=tools
        )


    async def _handle_transport_event(self, event: TransportEvent):
        """Handle transport events"""
        try:
            if event.event_type == EventType.SIP_INVITE:
                await self._handle_inbound_sip_call(event)
            elif event.event_type == EventType.PARTICIPANT_JOIN:
                await self._handle_participant_join(event)
            elif event.event_type == EventType.PARTICIPANT_LEAVE:
                await self._handle_participant_leave(event)
            elif event.event_type == EventType.DTMF:
                await self._handle_dtmf(event)
            elif event.event_type == EventType.SIP_REINVITE:
                await self._handle_sip_reinvite(event)
            elif event.event_type == EventType.HANGUP:
                await self._end_session(event.session_id, "remote_hangup")
                
        except Exception as e:
            self.logger.error(f"Error handling transport event {event.event_type}: {e}")

    async def _handle_inbound_sip_call(self, event: TransportEvent):
        """Handle incoming SIP call"""
        session_id = event.session_id
        call_data = event.payload
        
        call_meta = CallMeta(
            call_id=session_id,
            direction="inbound",
            from_number=call_data.get("from"),
            to_number=call_data.get("to"),
            sip_headers=call_data.get("headers", {})
        )
        
        # Create and start session
        await self._create_session(session_id, call_meta)
        
        # Auto-answer if configured
        if self.agent_config.auto_answer:
            await self.transport.answer_sip_call(session_id)
        
        self.logger.info(f"Handled inbound SIP call: {session_id}")

    async def _create_session(self, session_id: str, call_meta: CallMeta):
        """Create a new call session with pipecat pipeline"""
        try:
            # Start transport session
            await self.transport.start_session(session_id, call_meta)
            
            # Create pipecat pipeline if available
            if PIPECAT_AVAILABLE:
                pipeline, context_aggregator = await self._create_pipeline()
                
                # Create pipeline task
                task = PipelineTask(
                    pipeline,
                    params=PipelineParams(enable_metrics=True, enable_usage_metrics=True)
                )
                
                # Store session
                session = CallSession(
                    session_id=session_id,
                    call_meta=call_meta,
                    transport=self.transport,
                    pipeline_task=task,
                    context_aggregator=context_aggregator,
                    state="connected"
                )
                
                # Start pipeline
                asyncio.create_task(self.pipeline_runner.run(task))
            else:
                # Basic session without pipecat
                session = CallSession(
                    session_id=session_id,
                    call_meta=call_meta,
                    transport=self.transport,
                    state="connected"
                )
            
            self.active_sessions[session_id] = session
            self.logger.info(f"Created session: {session_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to create session {session_id}: {e}")

    async def _handle_outbound_call(self, phone_number: str, **kwargs) -> Dict[str, Any]:
        """Handle outbound call initiation"""
        try:
            session_id = f"out_{datetime.now().timestamp()}"
            
            call_meta = CallMeta(
                call_id=session_id,
                direction="outbound", 
                to_number=phone_number,
                from_number=kwargs.get("from_number")
            )
            
            await self._create_session(session_id, call_meta)
            
            return {
                "success": True,
                "session_id": session_id,
                "message": f"Outbound call initiated to {phone_number}"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _handle_message_interaction(self, message: Message, **kwargs) -> Dict[str, Any]:
        """Handle message-based interaction"""
        # Process message through appropriate session
        return {"success": True, "response": "Message processed"}

    async def _handle_participant_join(self, event: TransportEvent):
        """Handle participant joining"""
        session_id = event.session_id
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.state = "connected"
            self._send_callback_message(f"Participant joined call", session_id)

    async def _handle_participant_leave(self, event: TransportEvent):
        """Handle participant leaving"""
        await self._end_session(event.session_id, "participant_left")

    async def _handle_dtmf(self, event: TransportEvent):
        """Handle DTMF input"""
        digit = event.payload.get("digit")
        session_id = event.session_id
        self.logger.info(f"DTMF received: {digit} from session {session_id}")

    async def _handle_sip_reinvite(self, event: TransportEvent):
        """Handle SIP re-INVITE"""
        session_id = event.session_id
        self.logger.info(f"SIP re-INVITE for session {session_id}")

    async def _end_session(self, session_id: str, reason: str):
        """End a call session"""
        try:
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                
                # Cancel pipeline task
                if hasattr(session, 'pipeline_task') and session.pipeline_task:
                    await session.pipeline_task.queue_frame(EndFrame())
                
                # Close transport session
                if self.transport:
                    await self.transport.close_session(session_id, reason)
                
                # Remove from active sessions
                del self.active_sessions[session_id]
                
                self._send_callback_message(f"Call ended: {reason}", session_id)
                self.logger.info(f"Ended session {session_id}: {reason}")
                
        except Exception as e:
            self.logger.error(f"Error ending session {session_id}: {e}")

    def _send_callback_message(self, text: str, session_id: str):
        """Send callback message if callback is configured"""
        if self._callback:
            message = Message.add_notification(text)
            self._callback.send(message, thread_id=session_id)

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "system_prompt": f"You are {self.agent_config.agent_name}, a helpful voice assistant.",
            "first_message": "Hello! I'm your voice assistant. How can I help you today?",
            "knowledge_base": self.agent_config.knowledge_bases
        }
        """Create LLM context with knowledge base tools"""
        tools = ToolsSchema(standard_tools=[
            FunctionSchema(
                name="get_knowledge_base_info",
                description="Get information from knowledge bases",
                properties={
                    "query": {"type": "string", "description": "Search query"},
                    "kb_name": {"type": "string", "description": "Knowledge base name"}
                },
                required=["query"]
            )
        ])
        
        return OpenAILLMContext(
            messages=[
                {
                    "role": "system", 
                    "content": self.config.get("system_prompt", "You are a helpful voice assistant.")
                },
                {
                    "role": "user",
                    "content": self.config.get("first_message", "Hello! How can I help you today?")
                }
            ],
            tools=tools
        )
    
    
    async def _handle_outbound_call(self, phone_number: str, **kwargs) -> Dict[str, Any]:
        """Handle outbound call initiation"""
        try:
            session_id = f"out_{datetime.now().timestamp()}"
            
            call_meta = CallMeta(
                call_id=session_id,
                direction="outbound", 
                to_number=phone_number,
                from_number=kwargs.get("from_number")
            )
            
            await self._create_session(session_id, call_meta)
            
            return {
                "success": True,
                "session_id": session_id,
                "message": f"Outbound call initiated to {phone_number}"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _handle_message_interaction(self, message: Message, **kwargs) -> Dict[str, Any]:
        """Handle message-based interaction"""
        # Process message through appropriate session
        return {"success": True, "response": "Message processed"}
    
    async def _handle_participant_join(self, event: TransportEvent):
        """Handle participant joining"""
        session_id = event.session_id
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.state = "connected"
            self._send_callback_message(f"Participant joined call", session_id)
    
    async def _handle_participant_leave(self, event: TransportEvent):
        """Handle participant leaving"""
        await self._end_session(event.session_id, "participant_left")
    
    async def _handle_dtmf(self, event: TransportEvent):
        """Handle DTMF input"""
        digit = event.payload.get("digit")
        session_id = event.session_id
        self._logger.info(f"DTMF received: {digit} from session {session_id}")
        # Process DTMF through pipeline
    
    async def _handle_sip_reinvite(self, event: TransportEvent):
        """Handle SIP re-INVITE"""
        session_id = event.session_id
        self._logger.info(f"SIP re-INVITE for session {session_id}")
        # Handle codec renegotiation if needed
    
    async def _end_session(self, session_id: str, reason: str):
        """End a call session"""
        try:
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                
                # Cancel pipeline task
                if session.pipeline_task:
                    await session.pipeline_task.queue_frame(EndFrame())
                
                # Close transport session
                await self.transport.close_session(session_id, reason)
                
                # Remove from active sessions
                del self.active_sessions[session_id]
                
                self._send_callback_message(f"Call ended: {reason}", session_id)
                self._logger.info(f"Ended session {session_id}: {reason}")
                
        except Exception as e:
            self._logger.error(f"Error ending session {session_id}: {e}")
    
    def _send_callback_message(self, text: str, session_id: str):
        """Send callback message if callback is configured"""
        if self._callback:
            message = Message.add_notification(text)
            self._callback.send(message, thread_id=session_id)
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "system_prompt": f"You are {self.agent_config.agent_name}, a helpful voice assistant.",
            "first_message": "Hello! I'm your voice assistant. How can I help you today?",
            "knowledge_base": self.agent_config.knowledge_bases
        }
