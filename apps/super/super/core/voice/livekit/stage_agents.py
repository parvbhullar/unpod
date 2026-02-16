"""
Stage-based Agent classes for Conversation Intelligence.

This module provides specialized Agent classes for each conversation stage,
leveraging LiveKit's agent handoffs for stage transitions.

Each agent has:
- Focused instructions for its stage only
- on_enter() hook for stage-specific entry behavior
- Handoff tools to transition to next stage
- Access to shared `userdata` for state persistence

See: https://docs.livekit.io/agents/logic/agents-handoffs/
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, TYPE_CHECKING

from livekit.agents import Agent, function_tool, RunContext
from livekit.agents.llm import ChatContext

from super.core.voice.livekit.conversation_state import (
    ConversationUserData,
    ConversationStage,
)

if TYPE_CHECKING:
    from livekit.agents.voice import AgentSession


logger = logging.getLogger(__name__)


# Default conversational leadership rules for all agents
# NOTE: Also defined in prompt_manager.py - keep in sync
CONVERSATIONAL_LEADERSHIP_RULES = """
## CONVERSATIONAL LEADERSHIP (Always Active)

### Lead, Don't Wait
- Never end a turn with ONLY a question
- After asking, immediately provide context or options
- Example: "Kya aap interested hain? Actually, let me tell you about the three main benefits..."

### On User Acknowledgment
Forward-intent phrases: "yes", "haan", "ok", "sure", "theek hai", "go", "go ahead", "ahead",
"continue", "tell me", "tell me more", "proceed", "aage bolo", "batao", "chalo"

When user says ANY of these:
- Treat as "tell me more" - immediately provide NEW information
- Recommend one option explicitly
- Don't ask for clarification - assume forward intent
- NEVER repeat what you just said
- Example: User: "go ahead" → You: "Great! So here are the key benefits..." (NEW info, not repeat)

### CRITICAL: Never Repeat Content
- If user says "go", "ahead", "continue", etc. - provide NEXT piece of information
- If you already explained something, move to the next topic
- Track what you've said - never say the same pitch twice
- If user says "you already mentioned that" - apologize briefly and move forward
- Example: User: "you already said that" → You: "Apologies! Let me tell you about [new topic]..."

### Seamless Transitions
- Use bridge phrases: "Speaking of that...", "Iske saath...", "Aur ek baat..."
- Connect topics naturally, don't announce transitions
- Never say "Moving on to..." or "Now let's talk about..."

### Response Structure (Every Turn)
1. Acknowledge briefly (1-2 words max: "Bilkul", "Got it", "Sure")
2. Provide value/information immediately (NEW info, not repeated)
3. End with soft direction (not hard question)

### Anti-Patterns (NEVER DO)
- ❌ "Kya aap interested hain?" then wait silently
- ❌ "Could you clarify?" or "Kya matlab?" repeatedly
- ❌ "Is there anything else?" mid-conversation
- ❌ Repeating the same information twice (CRITICAL!)
- ❌ Ending with only a question and waiting
- ❌ Asking permission before every statement
- ❌ Saying the same pitch when user says "go" or "continue"

### Conversation Momentum
- Keep the conversation moving forward
- If user is quiet, provide the next logical piece of info
- Assume engagement unless explicitly told otherwise
"""


class BaseStageAgent(Agent, ABC):
    """
    Base class for stage-specific agents.
    
    Provides common functionality:
    - Config access
    - Chat context management
    - Custom system_prompt integration
    - Shared tool registration
    - Do-not-repeat context injection
    """
    
    def __init__(
        self,
        config: Dict[str, Any],
        chat_ctx: Optional[ChatContext] = None,
        **kwargs
    ):
        """
        Initialize stage agent.
        
        Args:
            config: Agent configuration (agent_name, company_name, system_prompt, etc.)
            chat_ctx: Optional chat context from previous agent
            **kwargs: Additional kwargs passed to parent Agent
        """
        self._config = config
        # Build instructions: custom system_prompt + stage-specific instructions
        instructions = self._build_full_instructions(config)
        super().__init__(instructions=instructions, chat_ctx=chat_ctx, **kwargs)
    
    def _build_full_instructions(self, config: Dict[str, Any]) -> str:
        """
        Build complete instructions by combining:
        1. Base prompt from PromptManager (includes voice rules, identity, dynamic context,
           AND CONVERSATIONAL_LEADERSHIP_RULES)
        2. Stage-specific instructions from subclass

        The base_prompt contains the full output from prompt_manager._create_assistant_prompt()
        which includes:
        - Voice rules (professional/casual/basic)
        - Agent identity with date/time
        - Dynamic context from user data
        - Follow-up and memory prompts
        - Custom system_prompt with template replacements
        - CONVERSATIONAL_LEADERSHIP_RULES (already included!)

        Args:
            config: Agent configuration (must include 'base_prompt')

        Returns:
            Complete instructions string
        """
        parts = []

        # Include base_prompt from PromptManager (full system prompt with all context)
        # NOTE: base_prompt already includes CONVERSATIONAL_LEADERSHIP_RULES from prompt_manager
        base_prompt = config.get("base_prompt", "")
        if base_prompt:
            parts.append(base_prompt)
        else:
            # Fallback: if no base_prompt, use system_prompt + leadership rules
            system_prompt = config.get("system_prompt", "")
            if system_prompt:
                parts.append(f"## Your Role & Context\n{system_prompt}")
            # Only add leadership rules in fallback case (base_prompt already has them)
            parts.append(CONVERSATIONAL_LEADERSHIP_RULES)

        # Add stage-specific instructions (conversation flow control)
        stage_instructions = self._build_instructions(config)
        parts.append(f"\n---\n## CURRENT STAGE INSTRUCTIONS\n{stage_instructions}")

        return "\n\n".join(parts)
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get agent configuration."""
        return self._config
    
    @property
    def agent_name(self) -> str:
        """Get agent display name."""
        return self._config.get("agent_name", "Assistant")
    
    @property
    def company_name(self) -> str:
        """Get company name."""
        return self._config.get("company_name", "")
    
    @abstractmethod
    def _build_instructions(self, config: Dict[str, Any]) -> str:
        """
        Build stage-specific instructions.
        
        Subclasses must implement to provide focused instructions.
        """
        pass
    
    @abstractmethod
    def get_stage_name(self) -> str:
        """Return the stage name for this agent."""
        pass
    
    def _get_do_not_repeat_context(self) -> str:
        """
        Get the do-not-repeat context from userdata.
        
        Should be injected into instructions to prevent repetition.
        """
        if hasattr(self, 'session') and self.session:
            userdata: ConversationUserData = self.session.userdata
            return userdata.get_do_not_repeat_summary()
        return ""
    
    async def on_enter(self) -> None:
        """
        Called when this agent becomes active.

        Subclasses can override to provide stage-specific entry behavior.
        Default: update current_stage in userdata and inject do-not-repeat context.
        """
        if hasattr(self, 'session') and self.session:
            userdata: ConversationUserData = self.session.userdata
            stage_name = self.get_stage_name()
            userdata.current_stage = stage_name
            userdata.increment_turn()

            # Record stage entry for quality metrics
            userdata.stage_timestamps[f"{stage_name}_enter"] = __import__('time').time()

            # Inject do-not-repeat context to prevent repetition
            do_not_repeat = userdata.get_do_not_repeat_summary()
            if do_not_repeat:
                try:
                    chat_ctx = self.chat_ctx.copy()
                    chat_ctx.add_message(role="system", content=do_not_repeat)
                    await self.update_chat_ctx(chat_ctx)
                    logger.info(f"Injected do-not-repeat context: {len(do_not_repeat)} chars")
                except Exception as e:
                    logger.warning(f"Failed to inject do-not-repeat context: {e}")

            # Log stage entry with quality metrics summary
            logger.info(
                f"Entered stage: {stage_name} | "
                f"turn={userdata.turn_count} | "
                f"completed_stages={len(userdata.completed_stages)}"
            )


class OpeningAgent(BaseStageAgent):
    """
    Opening stage: Greet user and get permission to continue.
    
    This is the initial agent for conversations.
    """
    
    def get_stage_name(self) -> str:
        return ConversationStage.OPENING.value
    
    def _build_instructions(self, config: Dict[str, Any]) -> str:
        call_type = config.get("call_type", "outbound")
        is_outbound = call_type == "outbound"
        
        return f"""You are {config.get('agent_name', 'Assistant')}, calling on behalf of {config.get('company_name', 'our company')}.

            ## Your Current Task: Opening
            {"- You initiated this call to the user" if is_outbound else "- User has called you"}
            - Greet warmly and briefly introduce yourself
            - {"Ask for permission to continue" if is_outbound else "Offer to help"}
            - DO NOT discuss product/service details yet
            - Keep responses under 15 words

            ## Voice Rules
            - Speak naturally, keep it brief
            - Acknowledge immediately (use fillers: "Got it", "Sure")
            - If user says "yes/ok/sure/haan", transition to context gathering
            - If user seems busy, offer to call back

            ## When to Proceed
            Use the `proceed_to_context_gathering` tool when:
            - User gives permission to continue
            - User asks what this is about
            - User shows interest
            """
    
    async def on_enter(self) -> None:
        await super().on_enter()

        # Get first_message from config (passed from model_config via **self.config)
        first_message = self._config.get("first_message")
        call_type = self._config.get("call_type", "outbound")

        # Build greeting instructions based on call_type
        if call_type == "outbound":
            # Outbound: Agent initiated the call, need to introduce and ask permission
            call_context = (
                "You are calling the user. "
                "Greet briefly, introduce why you're calling, and ask if they have a moment."
            )
        else:
            # Inbound: User called us, be helpful and welcoming
            call_context = (
                "The user has called you. "
                "Welcome them warmly and offer to help."
            )

        # Combine first_message with call context for better LLM guidance
        if first_message:
            greeting_instruction = f"{call_context}\n\nSay: {first_message}"
        else:
            greeting_instruction = call_context

        # Generate the greeting - agent speaks first to lead the conversation
        logger.info(f"[OPENING] call_type={call_type}, generating greeting...")
        await self.session.generate_reply(instructions=greeting_instruction)
    
    @function_tool(
        name="proceed_to_context_gathering",
        description="Proceed to understand user's needs after they show interest. Use when user says yes/ok/sure, asks what this is about, or expresses interest."
    )
    async def proceed_to_context_gathering(
        self,
        context: RunContext,
        reason: str = "user_permission"
    ):
        """
        User has given permission or showed interest. Proceed to understand their needs.

        Use this tool when:
        - User says yes/ok/sure
        - User asks what this is about
        - User expresses interest

        Args:
            reason: Why we're proceeding (for logging)
        """
        userdata: ConversationUserData = context.userdata
        userdata.mark_stage_complete(ConversationStage.OPENING.value)
        userdata.mark_content_delivered("introduction")
        userdata.mark_content_delivered("greeting")
        userdata.mark_content_delivered("permission_to_continue")

        logger.info(f"Proceeding to context gathering: {reason}")
        
        return ContextGatheringAgent(
            config=self._config,
            chat_ctx=self.chat_ctx
        ), "Great, let me understand how I can help you."
    
    @function_tool(
        name="offer_callback",
        description="User is busy. Offer to call back later at a specified or unspecified time."
    )
    async def offer_callback(
        self,
        context: RunContext,
        suggested_time: str = ""
    ):
        """
        User is busy. Offer to call back later.

        Args:
            suggested_time: When to call back (if specified)
        """
        return {
            "action": "schedule_callback",
            "time": suggested_time,
            "message": f"I'll call you back{' at ' + suggested_time if suggested_time else ' at a better time'}."
        }


class ContextGatheringAgent(BaseStageAgent):
    """
    Context gathering stage: Understand user's needs and lock intent.
    """
    
    def get_stage_name(self) -> str:
        return ConversationStage.CONTEXT_GATHERING.value
    
    def _build_instructions(self, config: Dict[str, Any]) -> str:
        return f"""You are {config.get('agent_name', 'Assistant')}.

        ## Your Current Task: Understanding Needs
        - Ask about their current situation
        - Identify their PRIMARY need
        - Ask ONE question at a time
        - DO NOT explain product details yet
        - When you clearly understand their need, use `lock_intent` tool

        ## DO NOT REPEAT
        Check the conversation context for "DO NOT REPEAT" instructions.
        These indicate stages/content already covered - never repeat them.

        ## Voice Rules
        - Keep questions under 15 words
        - Listen actively, acknowledge responses
        - If user mentions a specific need, record it

        ## When to Lock Intent
        Use `lock_intent` when:
        - User clearly states what they want
        - You've confirmed their primary interest
        - Intent confidence is high (>0.8)
        """
    
    async def on_enter(self) -> None:
        await super().on_enter()
    
    @function_tool(
        name="record_user_info",
        description="Record information about the user such as name, role, company, current situation, or specific needs."
    )
    async def record_user_info(
        self,
        context: RunContext,
        field_name: str,
        value: str
    ):
        """
        Record information about the user.

        Use this to capture:
        - Name, role, company
        - Current situation
        - Specific needs or preferences

        Args:
            field_name: What info this is (e.g., "role", "company", "current_challenge")
            value: The information value
        """
        userdata: ConversationUserData = context.userdata
        userdata.record_user_info(field_name, value)
        logger.info(f"Recorded user info: {field_name}={value}")
        return f"Noted: {field_name}"
    
    @function_tool(
        name="lock_intent",
        description="Lock the user's intent when clearly understood and proceed to value proposition. Use when user clearly stated their interest and no ambiguity remains."
    )
    async def lock_intent(
        self,
        context: RunContext,
        intent: str,
        confidence: float = 0.9
    ):
        """
        Lock the user's intent when clearly understood. Proceed to value proposition.

        Use this when:
        - User clearly stated their interest
        - You've confirmed what they want
        - No ambiguity remains

        Args:
            intent: The confirmed user intent (e.g., "career_growth", "product_inquiry")
            confidence: How confident you are (0.0-1.0)
        """
        userdata: ConversationUserData = context.userdata
        userdata.lock_intent(intent, confidence)
        userdata.mark_stage_complete(ConversationStage.CONTEXT_GATHERING.value)
        userdata.mark_content_delivered("discovery_questions")
        
        logger.info(f"Intent locked: {intent} (confidence={confidence})")
        
        return ValuePropositionAgent(
            config=self._config,
            chat_ctx=self.chat_ctx,
            locked_intent=intent
        ), f"I understand you're interested in {intent}."


class ValuePropositionAgent(BaseStageAgent):
    """
    Value proposition stage: Explain relevant value ONCE.
    """
    
    def __init__(
        self,
        config: Dict[str, Any],
        chat_ctx: Optional[ChatContext] = None,
        locked_intent: str = None,
        **kwargs
    ):
        self._locked_intent = locked_intent
        super().__init__(config=config, chat_ctx=chat_ctx, **kwargs)
    
    def get_stage_name(self) -> str:
        return ConversationStage.VALUE_PROPOSITION.value
    
    def _build_instructions(self, config: Dict[str, Any]) -> str:
        intent = self._locked_intent or "their needs"

        return f"""You are {config.get('agent_name', 'Assistant')}.

            ## Your Current Task: Explain Value
            - User's confirmed interest: **{intent}**
            - Explain how you can help with {intent}
            - Keep it concise (under 30 seconds of speech)
            - After explaining, proceed to close unless they have objections

            ## DO NOT REPEAT
            Check the conversation context for "DO NOT REPEAT" instructions.
            These indicate stages/content already covered - never repeat them.
            DO NOT re-explain the same value proposition twice.

            ## Intent Locked: {intent}
            - Do NOT re-ask "Is that what you're looking for?"
            - Do NOT re-confirm the intent
            - This is CONFIRMED. Move forward.

            ## Voice Rules
            - Be enthusiastic but concise
            - One value point, then check for questions
            - If no objections, proceed to close
            """
    
    async def on_enter(self) -> None:
        await super().on_enter()
        await self.session.generate_reply(
            instructions=f"Briefly explain how you can help with {self._locked_intent}. Keep under 30 words. Be specific and relevant."
        )
    
    @function_tool(
        name="handle_objection",
        description="User raised an objection or concern about price, timing, need, or trust. Address their concern."
    )
    async def handle_objection(
        self,
        context: RunContext,
        objection_type: str,
        objection_text: str = ""
    ):
        """
        User raised an objection or concern. Address it.

        Args:
            objection_type: Type of objection (price, timing, need, trust, etc.)
            objection_text: What the user actually said
        """
        userdata: ConversationUserData = context.userdata
        userdata.mark_content_delivered("value_explanation")
        
        return ObjectionHandlingAgent(
            config=self._config,
            chat_ctx=self.chat_ctx,
            objection_type=objection_type,
            objection_text=objection_text
        )
    
    @function_tool(
        name="proceed_to_close",
        description="Value delivered with no objections. Proceed to close when user acknowledges value or shows interest in next steps."
    )
    async def proceed_to_close(
        self,
        context: RunContext,
        reason: str = "value_accepted"
    ):
        """
        Value delivered, no objections. Proceed to close.

        Use when:
        - User acknowledges the value
        - User shows interest in next steps
        - No objections raised

        Args:
            reason: Why we're proceeding
        """
        userdata: ConversationUserData = context.userdata
        userdata.mark_stage_complete(ConversationStage.VALUE_PROPOSITION.value)
        userdata.mark_content_delivered("value_explanation")
        
        return ClosingAgent(
            config=self._config,
            chat_ctx=self.chat_ctx
        ), "Great! Let me help you take the next step."


class ObjectionHandlingAgent(BaseStageAgent):
    """
    Objection handling stage: Address user concerns.
    """
    
    def __init__(
        self,
        config: Dict[str, Any],
        chat_ctx: Optional[ChatContext] = None,
        objection_type: str = None,
        objection_text: str = None,
        **kwargs
    ):
        self._objection_type = objection_type
        self._objection_text = objection_text
        super().__init__(config=config, chat_ctx=chat_ctx, **kwargs)
    
    def get_stage_name(self) -> str:
        return ConversationStage.OBJECTION_HANDLING.value
    
    def _build_instructions(self, config: Dict[str, Any]) -> str:
        objection = self._objection_type or "concern"

        return f"""You are {config.get('agent_name', 'Assistant')}.

            ## Your Current Task: Address Objection
            - User's concern: **{objection}**
            - Acknowledge their concern genuinely
            - Address it concisely
            - DO NOT repeat value proposition

            ## DO NOT REPEAT
            Check the conversation context for "DO NOT REPEAT" instructions.
            These indicate stages/content already covered - never repeat them.

            ## Objection Handling Tips
            - Empathize first: "I understand..."
            - Address specifically
            - Offer alternatives if applicable
            - Then proceed to close

            ## Voice Rules
            - Stay calm and empathetic
            - Don't be defensive
            - Keep response focused
            """
    
    async def on_enter(self) -> None:
        await super().on_enter()
    
    @function_tool(
        name="objection_resolved",
        description="Objection has been addressed and resolved. Proceed to closing stage."
    )
    async def objection_resolved(
        self,
        context: RunContext,
        resolution: str = ""
    ):
        """
        Objection has been addressed. Proceed to close.

        Args:
            resolution: How the objection was resolved
        """
        userdata: ConversationUserData = context.userdata
        userdata.mark_stage_complete(ConversationStage.OBJECTION_HANDLING.value)
        userdata.mark_content_delivered("objection_response")
        
        return ClosingAgent(
            config=self._config,
            chat_ctx=self.chat_ctx
        ), "Great, I'm glad that helps."


class ClosingAgent(BaseStageAgent):
    """
    Closing stage: Confirm next steps and end gracefully.
    """
    
    def get_stage_name(self) -> str:
        return ConversationStage.CLOSING.value
    
    def _build_instructions(self, config: Dict[str, Any]) -> str:
        return f"""You are {config.get('agent_name', 'Assistant')}.

            ## Your Current Task: Close & Confirm
            - Confirm preferred contact method (WhatsApp/call/email)
            - Capture any missing info (number, time preference)
            - Set clear expectations
            - End politely

            ## CRITICAL: Do NOT Go Back
            Check the conversation context for "DO NOT REPEAT" instructions.
            All previous stages have been completed. Just close.

            ## Closing Checklist
            1. Confirm contact method
            2. Confirm contact info
            3. Set expectation (when they'll hear from you)
            4. Say goodbye warmly

            ## Voice Rules
            - Be warm and appreciative
            - Keep it brief
            - End on a positive note
            """
    
    async def on_enter(self) -> None:
        await super().on_enter()
    
    @function_tool(
        name="confirm_contact_method",
        description="Confirm how user wants to be contacted via whatsapp, call, or email."
    )
    async def confirm_contact_method(
        self,
        context: RunContext,
        method: str,
        contact_info: str = ""
    ):
        """
        Confirm how user wants to be contacted.

        Args:
            method: Contact method (whatsapp, call, email)
            contact_info: Their contact info if provided
        """
        userdata: ConversationUserData = context.userdata
        userdata.record_user_info("contact_method", method)
        if contact_info:
            userdata.record_user_info("contact_info", contact_info)
        
        return f"I'll reach you via {method}."
    
    @function_tool(
        name="end_call",
        description="End the call gracefully when user confirms they're done, next steps are confirmed, or user says goodbye."
    )
    async def end_call(
        self,
        context: RunContext,
        reason: str = "conversation_complete"
    ):
        """
        End the call gracefully.

        Use when:
        - User confirms they're done
        - Next steps are confirmed
        - User says goodbye

        Args:
            reason: Why call is ending
        """
        userdata: ConversationUserData = context.userdata
        userdata.mark_stage_complete(ConversationStage.CLOSING.value)

        # Get quality metrics for logging
        quality_metrics = userdata.get_quality_metrics()

        # Log quality summary
        logger.info(f"Call ending: {reason}")
        logger.info(userdata.get_quality_log_line())
        logger.info(
            f"[CONV_END] "
            f"intent={quality_metrics.get('intent', 'none')} | "
            f"stages={quality_metrics['stages_completed']}/{len(ConversationStage)} | "
            f"score={quality_metrics['scores']['overall']}"
        )

        # Persist quality metrics to JSONL file
        filepath = userdata.persist_quality_metrics(reason=reason)
        if filepath:
            logger.info(f"Quality metrics persisted to: {filepath}")

        return {
            "action": "end_call",
            "reason": reason,
            "user_profile": userdata.user_profile,
            "completed_stages": list(userdata.completed_stages),
            "quality_metrics": quality_metrics,
        }


# Factory function to get initial agent based on config
def create_initial_agent(config: Dict[str, Any]) -> BaseStageAgent:
    """
    Create the initial stage agent based on configuration.
    
    Args:
        config: Agent configuration
        
    Returns:
        OpeningAgent as the default starting point
    """
    return OpeningAgent(config=config)
