"""
Prompt Manager Module for Pipecat Voice Handler

This module contains all prompt and context creation logic extracted from the
PipecatVoiceHandler class. It provides a standalone PromptManager class that
handles:
- Context creation with tools
- Assistant prompt generation with language support
- Multilingual message templates

Author: Extracted from pipecat.py
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any

from super.core.voice.prompts.legacy.basic import BASIC_PROMPT
from super.core.voice.prompts.legacy.casual import CASUAL_PROMPT
from super.core.voice.prompts.legacy.professional import PROFESSIONAL_PROMPT
from super.core.voice.prompts.legacy.guidelines_prompt import (
    MEMORY_PROMPT,
    FOLLOW_UP_PROMPT,
)
from super.core.voice.prompts.composer import create_prompt_from_agent_config
from super.core.voice.managers.tools_manager import ToolsManager
from super.core.voice.services.service_common import (
    get_model_context_limit,
    estimate_tokens,
)


# Dashboard interpretation rules for observational context injection
DASHBOARD_INTERPRETATION_RULES = """
---
## How to Use [CONVERSATION STATUS]

You'll receive a status dashboard each turn. Use it to understand where you are, not what to say.

### Reading the Checklist
- [✓] = Already covered. DO NOT repeat these topics.
- [ ] = Not yet covered. Weave these in naturally when relevant.
- You don't need to cover topics in order. Follow the conversation flow.

### Reading the Goal
- "pending" = Haven't asked yet. Look for natural moment to bring it up.
- "attempted" = Already asked. If declined, try a different angle once.
- "achieved" = Success! Move to confirm details and close.

### What NOT to Do
- Do not repeat [✓] topics
- Do not force topics - let conversation flow
- Do not read the checklist out loud
- Do not say "According to my checklist..."
- Do not ignore user's question to push agenda


---
"""

# Default conversational leadership rules for all voice agents
CONVERSATIONAL_LEADERSHIP_RULES = """
---
## CONVERSATIONAL LEADERSHIP (Always Active)

### Lead, Don't Wait
- Never end a turn with ONLY a question
- After asking, immediately provide context or options
- Example: "Kya aap interested hain? Actually, let me tell you about the three main benefits..."

### On User Acknowledgment
Forward-intent phrases: "yes", "haan", "ok", "sure", "theek hai", "go", "go ahead", "ahead",
"continue", "tell me", "tell me more", "proceed", "aage bolo", "batao", "chalo"

### Language Mirroring
- Understand the language of the user and reflect back while speaking
- Match user's language in your response if user talk in Hindi then you should talk in Hinglish or Hindi
- If user talks in English then you should talk in English

### Conversation Style
- Be natural, not scripted
- One topic at a time, brief responses (under 25 words spoken)
- If user asks a question, answer it before continuing your agenda
- Don't announce topics ("Now let me tell you about pricing...")
- Use natural bridges ("Speaking of that...", "Aur ek baat...")

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
- After every full stop, add break tag <break time="200ms"/> or filler: "uh", "um", "achha", "theek hai", "right", "so", "toh"

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

### Voice Output (CRITICAL - MUST FOLLOW)
Your output is spoken aloud by TTS. Markdown will be read literally as "asterisk asterisk".

FORBIDDEN formatting:
- No **bold** or *italics* (TTS says "asterisk asterisk")
- No numbered lists: 1. 2. 3.
- No bullet points: - • *
- No headers: # ## ###

INCORRECT: "We offer: 1. **General Studies**: Available in one-year and two-year programs. 2. **CSAT**: A focused course..."
CORRECT: "We have General Studies available in one-year and two-year programs. We also offer CSAT which is a focused course..."

WRONG: "The key features are: - **Expert faculty** - **Study materials** - **Test series**"
RIGHT: "The key features include expert faculty, comprehensive study materials, and regular test series."

WRONG: "# Our Programs\n**Classroom Mode**: Best for..."
RIGHT: "Let me tell you about our programs. Classroom mode is best for..."

Speak lists naturally:
- "First option is X, then there's Y, and also Z"
- "We have three modes: Classroom, Online, and Hybrid"
- "The main benefits are faculty support, materials, and test series"

## REFLECTION
- Reflect on the conversation and provide the next logical piece of info
---
"""

# Pipecat imports
try:
    from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
    from pipecat.adapters.schemas.function_schema import FunctionSchema
    from pipecat.adapters.schemas.tools_schema import ToolsSchema
    from pipecat.transcriptions.language import Language

    PIPECAT_AVAILABLE = True
except ImportError:
    PIPECAT_AVAILABLE = False
    OpenAILLMContext = None
    FunctionSchema = None
    ToolsSchema = None
    Language = None


class PromptManager:
    """
    Manages prompt creation, context building, and message templates for voice agents.

    This class encapsulates all logic related to:
    - Creating LLM contexts with configured tools
    - Generating assistant prompts with timezone awareness
    - Supporting multiple Indian languages (Hindi, Punjabi, Tamil, Urdu)
    - Providing multilingual message templates
    - Template parameter replacement (e.g., {{username}}, {{contact_number}})
    """

    def __init__(
        self,
        config: Dict[str, Any],
        agent_config: Optional[Any] = None,
        session_id: Optional[str] = None,
        tool_calling: bool = True,
        logger: Optional[logging.Logger] = None,
        user_state: Optional[Any] = None,
    ):
        """
        Initialize the PromptManager.

        Args:
            config: Configuration dictionary containing system_prompt, language,
                   first_message, knowledge_bases, handover_number, etc.
            agent_config: Agent configuration object with agent_name attribute
            session_id: Unique session identifier
            tool_calling: Whether to enable tool calling functionality
            logger: Logger instance for logging
            user_state: User state object containing dynamic data for template replacement
        """
        self.config = config
        self.agent_config = agent_config
        self._session_id = session_id or "Unknown"
        self._tool_calling = tool_calling
        self._logger = logger or logging.getLogger(__name__)
        self.user_state = user_state
        self.input_data = None  # Will be set externally with call input data
        self.use_flows = config.get("use_flows", False)

        # Set defaults for new conversational prompt system
        self.config.setdefault("use_conversational_prompts", True)
        self.config.setdefault("agent_tone", "professional")

        # Validate pipecat availability
        if not PIPECAT_AVAILABLE:
            self._logger.warning(
                "Pipecat is not available. Some functionality may be limited."
            )

    def _build_template_data(
        self, additional_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build a unified dictionary containing all available template data.

        Merges data from config, user_state, agent_config, and additional_data.
        Priority order (highest to lowest):
        1. additional_data (passed parameter)
        2. user_state attributes
        3. config dictionary
        4. agent_config attributes
        5. Built-in values (session_id)

        Args:
            additional_data: Optional dictionary with highest priority values

        Returns:
            Unified dictionary with all available template values
        """
        template_data = {}

        # Start with built-in values (lowest priority)
        template_data["session_id"] = self._session_id

        # Add agent_config values
        if self.agent_config and hasattr(self.agent_config, "agent_name"):
            template_data["agent_name"] = self.agent_config.agent_name

        # Add config values
        if self.config:
            template_data.update(self.config)

        # Add input_data (call input data from task.input)
        if self.input_data and isinstance(self.input_data, dict):
            template_data.update(self.input_data)

        # Add user_state values (both as dict and attributes)
        if self.user_state:
            # Try dictionary access first
            if hasattr(self.user_state, "__getitem__") and hasattr(
                self.user_state, "keys"
            ):
                try:
                    template_data.update(dict(self.user_state))
                except (TypeError, ValueError):
                    pass

            # Add common attributes if they exist
            for attr in [
                "user_name",
                "username",
                "contact_number",
                "phone_number",
                "email",
                "first_name",
                "last_name",
                "company",
                "address",
            ]:
                if hasattr(self.user_state, attr):
                    value = getattr(self.user_state, attr)
                    if value is not None:
                        template_data[attr] = value

            # Add extra_data from user_state (contains dynamic fields from task.input)
            if hasattr(self.user_state, "extra_data") and self.user_state.extra_data:
                if isinstance(self.user_state.extra_data, dict):
                    template_data.update(self.user_state.extra_data)

        # Add additional_data (highest priority)
        if additional_data:
            template_data.update(additional_data)

        # Add common parameter variations for better compatibility
        if "user_name" in template_data and "username" not in template_data:
            template_data["username"] = template_data["user_name"]
        elif "username" in template_data and "user_name" not in template_data:
            template_data["user_name"] = template_data["username"]

        if "contact_number" in template_data and "phone_number" not in template_data:
            template_data["phone_number"] = template_data["contact_number"]
        elif "phone_number" in template_data and "contact_number" not in template_data:
            template_data["contact_number"] = template_data["phone_number"]

        return template_data

    def _replace_template_params(
        self, text: str, data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Replace template parameters in text with actual values from provided data.

        This optimized version:
        - Only processes parameters that actually exist in the text
        - Uses a unified data source for faster lookups
        - Reduces redundant checks and iterations

        Args:
            text: Text containing template parameters (e.g., "Hello {{username}}, your number is {{contact_number}}")
            data: Optional dictionary with template values (takes highest priority)

        Returns:
            Text with template parameters replaced with actual values

        Example:
            # >>> manager._replace_template_params(
            # ...     "Hello {{name}}, your order {{order_id}} is ready",
            # ...     {"name": "John", "order_id": "12345"}
            # ... )
            "Hello John, your order 12345 is ready"
        """
        if not text or "{{" not in text:
            return text

        import re

        # Find all unique template parameters in the text
        template_pattern = r"\{\{([^}]+)\}\}"
        param_matches = re.findall(template_pattern, text)

        if not param_matches:
            return text

        # Build unified data dictionary once
        template_data = self._build_template_data(data)

        # Add user_data from extra_data if available
        if (
            self.user_state
            and hasattr(self.user_state, "extra_data")
            and isinstance(self.user_state.extra_data, dict)
            and self.user_state.extra_data.get("user_data")
        ):
            user_data = self.user_state.extra_data.get("user_data")
            if isinstance(user_data, dict):
                template_data.update(user_data)
                self._logger.debug(f"Added user_data keys to template: {list(user_data.keys())}")

        # Replace each unique parameter
        replaced_text = text
        processed_params = set()  # Track processed params to avoid duplicates

        for param in param_matches:
            param_key = param.strip()

            # Skip if already processed (for efficiency)
            if param_key in processed_params:
                continue

            processed_params.add(param_key)

            # Look up value in unified data dictionary
            value = template_data.get(param_key)

            if value is not None:
                # Convert value to string and replace {{param_key}} with actual value
                value_str = str(value)
                replaced_text = replaced_text.replace(f"{{{{{param_key}}}}}", value_str)
                self._logger.debug(f"Replaced {{{{{param_key}}}}} with: {value_str}")

            else:
                self._logger.warning(
                    f"Template parameter {{{{{{{param}}}}}}} not found in available data. Keeping as-is."
                )

        return replaced_text

    def _create_context_with_tools(self) -> Optional[Any]:
        """
        Create LLM context with knowledge base tools.

        This method builds an OpenAI LLM context with:
        - System and assistant messages
        - Optional knowledge base retrieval tool (get_docs)
        - Optional call handover tool (handover_call)

        Returns:
            OpenAILLMContext object or None if pipecat is not available
        """
        if not PIPECAT_AVAILABLE:
            self._logger.warning("Cannot create context: Pipecat is not available")
            return None

        # Build tools list using ToolsManager
        tools_manager = ToolsManager(self.config)
        standard_tools = tools_manager.build_function_schemas()

        # Get first message and replace template parameters
        first_message = self.config.get(
            "first_message", "Hello! How can I help you today?"
        )
        first_message = self._replace_template_params(first_message)

        # Create system prompt
        system_prompt = self._create_assistant_prompt()

        # Context messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "assistant", "content": first_message},
        ]

        # Log context info for debugging
        llm_model = self.config.get("llm_model", "gpt-4o-mini")
        context_limit = get_model_context_limit(llm_model)
        system_tokens = estimate_tokens(system_prompt)
        self._logger.info(
            f"Context limit: {context_limit} tokens, system prompt: {system_tokens} tokens "
            f"(model: {llm_model})"
        )

        if self._tool_calling and len(standard_tools) > 0:
            # Convert FunctionSchema objects to dicts for JSON serialization
            tools = ToolsSchema(standard_tools=standard_tools)
            context = OpenAILLMContext(
                messages=messages,
                tools=tools,
            )
            self._logger.info(f"Context created with tools (context_limit={context_limit})")
        else:
            context = OpenAILLMContext(
                messages=messages,
            )
            self._logger.info(f"Context created without tools (context_limit={context_limit})")

        return context

    def _create_assistant_prompt(self) -> str:
        """
        Create assistant prompt from config.

        This method generates a comprehensive system prompt that includes:
        - Current date/time in IST
        - Agent identity and session information
        - Language and communication guidelines
        - Phoneme support for Indian languages
        - Natural speech patterns and fillers
        - Custom persona prompt from config

        If use_conversational_prompts is enabled, uses the new modular
        tone-based prompt system for more natural conversations.

        Returns:
            Complete system prompt string
        """
        # Get current time in UTC+5:30 (Indian Standard Time)
        ist = timezone(timedelta(hours=5, minutes=30))
        current_time = datetime.now(ist)
        current_date = current_time.strftime("%A, %B %d, %Y")
        current_time_str = current_time.strftime("%I:%M %p IST")

        # Check for new conversational prompts feature flag
        if self.config.get("use_conversational_prompts", False):
            return self._create_conversational_prompt(current_date, current_time_str)

        # Get agent details
        agent_name = (
            self.agent_config.agent_name
            if hasattr(self.agent_config, "agent_name")
            else "Voice Assistant"
        )
        session_id = self._session_id

        gender = self.config.get("gender", "Female")
        ag_timezone = self.config.get("timezone", "Indian Standard Time (UTC+5:30)")
        preferred_language = self.config.get("preferred_language") or self.config.get(
            "language", "en"
        )
        ln = self.get_human_language(preferred_language)
        call_type = self.config.get("call_type", "outbound")
        call_type_instruction = (
            "You are calling to a person over phone"
            if call_type == "outbound"
            else "You are receiving a call from a person"
        )

        self._logger.info(
            f"Creating assistant - {agent_name}, {ln}, {gender}, {call_type}, {ag_timezone}"
        )
        # Optimized prompt: reduced from ~1500 tokens to ~400 tokens
        transcript_prompt = ""
        agent_tone = self.config.get("agent_tone", "professional")
        if agent_tone == "professional":
            transcript_prompt += PROFESSIONAL_PROMPT
        elif agent_tone == "casual":
            transcript_prompt += CASUAL_PROMPT
        else:
            transcript_prompt += BASIC_PROMPT

        # Phoneme definitions removed to reduce token count from ~800 to ~50 tokens
        # TTS services (Cartesia, ElevenLabs, etc.) handle pronunciation automatically
        # Only add if explicitly required by config
        if self.config.get("include_phonemes", False):
            transcript_prompt += "\n### Phoneme Support: IPA-style pronunciation for Indian languages enabled\n"

        transcript_prompt += f"""
        # [Voice Agent Identity]- {agent_name}
        **Date:** {current_date} {current_time_str} | **Agent Gender:** {gender}
        **Remember:** {call_type_instruction}
        **Timezone:** {ag_timezone}
        """

        transcript_prompt += "\n---\n**PERSONA_PROMPT**:\n\n"

        # Append custom system prompt from config and replace template parameters
        use_section_based = self.use_flows
        if use_section_based:
            system_prompt = (
                "Please follow the defined conversation sections and flow structure."
            )
        else:
            system_prompt = self.config.get(
                "system_prompt", "Hello! How can I help you today?"
            )
            system_prompt = self._replace_template_params(system_prompt)

        # Inject dynamic fields from extra_data/input_data as customer context
        # This ensures the LLM knows about custom fields even without template variables
        dynamic_context = self._build_dynamic_context()
        if dynamic_context:
            system_prompt = f"{system_prompt}\n\n{dynamic_context}"
        if self.user_state.model_config.get("follow_up_enabled"):
            transcript_prompt += FOLLOW_UP_PROMPT

        if self.user_state.model_config.get("enable_memory"):
            transcript_prompt += MEMORY_PROMPT

        # Add dashboard interpretation and conversational leadership rules
        # transcript_prompt += DASHBOARD_INTERPRETATION_RULES
        transcript_prompt += CONVERSATIONAL_LEADERSHIP_RULES

        assistant_prompt = transcript_prompt + system_prompt

        # Replace any remaining template params from user_data
        if (
            self.user_state
            and hasattr(self.user_state, "extra_data")
            and isinstance(self.user_state.extra_data, dict)
            and self.user_state.extra_data.get("user_data")
        ):
            user_data = self.user_state.extra_data.get("user_data")
            if isinstance(user_data, dict):
                for key, value in user_data.items():
                    if value is not None:
                        assistant_prompt = assistant_prompt.replace(
                            f"{{{{{key}}}}}", str(value)
                        )


        return assistant_prompt

    def _create_conversational_prompt(
        self, current_date: str, current_time_str: str
    ) -> str:
        """
        Create assistant prompt using the new modular conversational system.

        This method uses the tone-based prompt composer for more natural,
        example-driven conversation flows optimized for voice interactions.

        Args:
            current_date: Formatted current date string
            current_time_str: Formatted current time string

        Returns:
            Complete conversational system prompt string
        """
        # Get agent name
        agent_name = (
            self.agent_config.agent_name
            if hasattr(self.agent_config, "agent_name")
            else "Voice Assistant"
        )

        # Get system prompt (custom persona) and replace template params
        use_section_based = self.use_flows
        if use_section_based:
            custom_persona = (
                "Please follow the defined conversation sections and flow structure."
            )
        else:
            custom_persona = self.config.get("system_prompt", "")
            custom_persona = self._replace_template_params(custom_persona)

        # Inject dynamic context into custom persona
        dynamic_context = self._build_dynamic_context()
        if dynamic_context:
            custom_persona = f"{custom_persona}\n\n{dynamic_context}"

        # Build config dict for composer
        composer_config = {
            "company_name": self.config.get("company_name", ""),
            "agent_tone": self.config.get("agent_tone", "professional"),
            "preferred_language": self.config.get("stt_language")
            or self.config.get("preferred_language")
            or self.config.get("language", "en"),
            "call_type": self.config.get("call_type", "inbound"),
            "enable_memory": (
                self.user_state.model_config.get("enable_memory", False)
                if self.user_state and hasattr(self.user_state, "model_config")
                else False
            ),
            "follow_up_enabled": (
                self.user_state.model_config.get("follow_up_enabled", False)
                if self.user_state and hasattr(self.user_state, "model_config")
                else False
            ),
            # Pattern flags - can be configured explicitly
            "include_sales_patterns": self.config.get("include_sales_patterns", False),
            "include_booking_patterns": self.config.get(
                "include_booking_patterns", False
            ),
        }

        # Create prompt using composer
        prompt = create_prompt_from_agent_config(
            config=composer_config,
            agent_name=agent_name,
            current_datetime=f"{current_date} {current_time_str}",
            custom_persona=custom_persona if custom_persona else None,
        )

        # Add dashboard interpretation and conversational leadership rules
        prompt += DASHBOARD_INTERPRETATION_RULES
        prompt += CONVERSATIONAL_LEADERSHIP_RULES

        self._logger.info(
            f"Created conversational prompt for {agent_name} "
            f"(tone={composer_config['agent_tone']}, "
            f"lang={composer_config['preferred_language']})"
        )

        return prompt

    def _build_dynamic_context(self) -> str:
        """
        Build a dynamic context string from extra_data/input_data.

        This method extracts custom fields from user_state.extra_data or input_data
        and formats them as a context block that can be appended to the system prompt.
        This allows the LLM to know about customer-specific data without requiring
        explicit template variables in the system prompt.

        Returns:
            Formatted context string, or empty string if no dynamic data available
        """
        # Keys to exclude from dynamic context (internal/system fields)
        exclude_keys = {
            "vapi_agent_id",
            "quality",
            "call_type",
            "token",
            "agent_id",
            "document_id",
            "created",
            "objective",
            "thread_id",
            "space_name",
            "contact_number",  # Already available in user_state
            "contact_name",  # Already available as user_name
            "name",  # Already available as user_name
        }

        # Collect dynamic fields from extra_data and input_data
        dynamic_fields = {}

        # Get from input_data first
        if self.input_data and isinstance(self.input_data, dict):
            for key, value in self.input_data.items():
                if key not in exclude_keys and value is not None and str(value).strip():
                    dynamic_fields[key] = value

        # Get from user_state.extra_data (may override input_data)
        if self.user_state and hasattr(self.user_state, "extra_data"):
            if isinstance(self.user_state.extra_data, dict):
                for key, value in self.user_state.extra_data.items():
                    if (
                        key not in exclude_keys
                        and value is not None
                        and str(value).strip()
                    ):
                        dynamic_fields[key] = value

        if not dynamic_fields:
            return ""

        # Format as context block
        context_lines = ["---", "## Customer/User Information (from call data):"]
        for key, value in dynamic_fields.items():
            # Convert key from snake_case to Title Case for readability
            readable_key = key.replace("_", " ").title()
            context_lines.append(f"- **{readable_key}**: {value}")

        context_lines.append("---")
        context_lines.append(
            "Use the above customer information when responding to queries about their details."
        )

        return "\n".join(context_lines)

    def _is_domain_relevant(self, text: str) -> bool:
        KEYWORDS = []
        if not text:
            return True
        lowered = text.lower()
        return any(keyword in lowered for keyword in KEYWORDS)

    def _inject_domain_guardrail(self, text: str) -> str:
        guardrail = (
            "System note: Answer strictly with persona related things only."
            "Politely decline other topics and redirect back to context."
        )
        if guardrail in text:
            return text
        return f"{text}\n\n{guardrail}"

    def _should_enforce_english(self) -> bool:
        preferred = (self.config or {}).get("language", "en")
        return isinstance(preferred, str) and preferred.lower().startswith("en")

    def _needs_language_correction(self, text: str) -> bool:
        if not text or not self._should_enforce_english():
            return False
        alpha_chars = [ch for ch in text if ch.isalpha()]
        if not alpha_chars:
            return False
        ascii_chars = [ch for ch in alpha_chars if ch.isascii()]
        ratio = len(ascii_chars) / len(alpha_chars)
        return ratio < 0.85

    def get_service_language(self, language: str) -> Optional[Any]:
        """
        Convert language code to Pipecat Language enum.

        Dynamically builds a map of all available Language enum values,
        supporting both simple codes (e.g., "hi") and region-specific codes (e.g., "hi-IN").

        Args:
            language: Language code string (e.g., "hi", "pa", "ta", "ur", "en-US")

        Returns:
            Pipecat Language enum value or Language.EN as default
        """
        if not PIPECAT_AVAILABLE or not Language:
            self._logger.warning("Pipecat Language not available, returning None")
            return None

        # Dynamically build language map from Language enum
        language_map = {}
        for lang_attr in dir(Language):
            if not lang_attr.startswith("_"):
                try:
                    lang_enum = getattr(Language, lang_attr)
                    # Map both the enum name and its value to the enum
                    # e.g., "HI" -> Language.HI and "hi" -> Language.HI
                    language_map[lang_attr.lower()] = lang_enum
                    language_map[lang_enum.value.lower()] = lang_enum
                except (AttributeError, ValueError):
                    continue

        # Normalize input and lookup
        normalized_lang = language.lower() if language else ""
        return language_map.get(normalized_lang, Language.EN)

    def get_human_language(self, language: str) -> Optional[str]:
        """
        Convert language code or Language enum to human-readable language name.

        Dynamically generates human-readable names for all available Language enum values.
        Supports both Language enum objects and string codes.

        Args:
            language: Language code string (e.g., "hi", "pa", "ta", "ur") or Language enum

        Returns:
            Human-readable language name string (e.g., "Hindi", "Punjabi") or "English" as default
        """
        if not PIPECAT_AVAILABLE or not Language:
            self._logger.warning("Pipecat Language not available, returning default")
            return "English"

        # Comprehensive mapping of language codes to human-readable names
        # This covers all major languages in the Language enum
        human_names = {
            "af": "Afrikaans",
            "am": "Amharic",
            "ar": "Arabic",
            "as": "Assamese",
            "ast": "Asturian",
            "az": "Azerbaijani",
            "ba": "Bashkir",
            "be": "Belarusian",
            "bg": "Bulgarian",
            "bn": "Bengali",
            "bo": "Tibetan",
            "br": "Breton",
            "bs": "Bosnian",
            "ca": "Catalan",
            "ceb": "Cebuano",
            "cmn": "Mandarin Chinese",
            "cs": "Czech",
            "cy": "Welsh",
            "da": "Danish",
            "de": "German",
            "el": "Greek",
            "en": "English",
            "eo": "Esperanto",
            "es": "Spanish",
            "et": "Estonian",
            "eu": "Basque",
            "fa": "Persian",
            "ff": "Fulah",
            "fi": "Finnish",
            "fil": "Filipino",
            "fo": "Faroese",
            "fr": "French",
            "ga": "Irish",
            "gd": "Gaelic",
            "gl": "Galician",
            "gu": "Gujarati",
            "ha": "Hausa",
            "haw": "Hawaiian",
            "he": "Hebrew",
            "hi": "Hindi",
            "hn": "Hinglish",
            "hr": "Croatian",
            "ht": "Haitian Creole",
            "hu": "Hungarian",
            "hy": "Armenian",
            "id": "Indonesian",
            "ig": "Igbo",
            "is": "Icelandic",
            "it": "Italian",
            "iu": "Inuktitut",
            "ja": "Japanese",
            "jv": "Javanese",
            "jw": "Javanese",
            "ka": "Georgian",
            "kea": "Kabuverdianu",
            "kk": "Kazakh",
            "km": "Khmer",
            "kn": "Kannada",
            "ko": "Korean",
            "ku": "Kurdish",
            "ky": "Kyrgyz",
            "la": "Latin",
            "lb": "Luxembourgish",
            "ln": "Lingala",
            "lo": "Lao",
            "lt": "Lithuanian",
            "lg": "Ganda",
            "luo": "Luo",
            "lv": "Latvian",
            "mg": "Malagasy",
            "mi": "Maori",
            "mk": "Macedonian",
            "ml": "Malayalam",
            "mn": "Mongolian",
            "mr": "Marathi",
            "ms": "Malay",
            "mt": "Maltese",
            "my": "Burmese",
            "mymr": "Burmese",
            "nb": "Norwegian Bokmål",
            "ne": "Nepali",
            "nl": "Dutch",
            "nn": "Norwegian Nynorsk",
            "no": "Norwegian",
            "nso": "Northern Sotho",
            "ny": "Chichewa",
            "oc": "Occitan",
            "or": "Odia",
            "pa": "Punjabi",
            "pl": "Polish",
            "ps": "Pashto",
            "pt": "Portuguese",
            "ro": "Romanian",
            "ru": "Russian",
            "sa": "Sanskrit",
            "sd": "Sindhi",
            "si": "Sinhala",
            "sk": "Slovak",
            "sl": "Slovenian",
            "sn": "Shona",
            "so": "Somali",
            "sq": "Albanian",
            "sr": "Serbian",
            "su": "Sundanese",
            "sv": "Swedish",
            "sw": "Swahili",
            "ta": "Tamil",
            "te": "Telugu",
            "tg": "Tajik",
            "th": "Thai",
            "tk": "Turkmen",
            "tl": "Tagalog",
            "tr": "Turkish",
            "tt": "Tatar",
            "ug": "Uyghur",
            "uk": "Ukrainian",
            "umb": "Umbundu",
            "ur": "Urdu",
            "uz": "Uzbek",
            "vi": "Vietnamese",
            "wo": "Wolof",
            "wuu": "Wu Chinese",
            "xh": "Xhosa",
            "yi": "Yiddish",
            "yo": "Yoruba",
            "yue": "Cantonese",
            "zh": "Chinese",
            "zu": "Zulu",
        }

        # If input is a Language enum, extract its base language code
        if hasattr(language, "value"):
            lang_code = language.value
        else:
            lang_code = language

        # Extract base language code (e.g., "en" from "en-US", "hi" from "hi-IN")
        if isinstance(lang_code, str):
            base_code = lang_code.split("-")[0].lower()
            return human_names.get(base_code, "English")

        return "English"

    def get_message(self, user_language: str, param: str) -> str:
        """
        Get message based on language and param.

        Provides multilingual message templates for common call scenarios:
        - call_start: Call connection message
        - call_end: Call termination message
        - call_error: Error message
        - idle_warning_1: First idle warning
        - idle_warning_2: Second idle warning
        - idle_disconnect: Final disconnect message

        Args:
            user_language: Language code ("en", "hi", etc.)
            param: Message parameter/key

        Returns:
            Localized message string or empty string if not found
        """
        messages = {
            "en": {
                "call_start": "Connecting your call, please wait...",
                "call_end": "Thank you for calling. Goodbye!",
                "call_error": "We're sorry, but there was an error connecting your call.",
                "idle_warning_1": "Are you still there? ",
                "idle_warning_2": "Would you like to continue our conversation?",
                "idle_disconnect": "No response detected. Ending the call now.",
            },
            "hi": {
                "call_start": "आपके कॉल को कनेक्ट किया जा रहा है, कृपया प्रतीक्षा करें...",
                "call_end": "कॉल के लिए धन्यवाद। अलविदा!",
                "call_error": "क्षमा करें, लेकिन आपके कॉल को कनेक्ट करने में त्रुटि हुई है।",
                "idle_warning_1": "क्या आप अभी भी यहाँ हैं?",
                "idle_warning_2": "क्या आप हमारी बातचीत जारी रखना चाहेंगे?",
                "idle_disconnect": "कोई response नहीं मिला। अब कॉल समाप्त कर रही हूँ।",
            },
            # Add more languages as needed
        }

        lang = user_language if user_language in messages else "en"
        return messages[lang].get(param, "")

    def update_config(self, config: Dict[str, Any]) -> None:
        """
        Update the configuration dictionary.

        Args:
            config: New configuration dictionary
        """
        self.config = config

    def update_agent_config(self, agent_config: Any) -> None:
        """
        Update the agent configuration object.

        Args:
            agent_config: New agent configuration object
        """
        self.agent_config = agent_config

    def update_session_id(self, session_id: str) -> None:
        """
        Update the session ID.

        Args:
            session_id: New session identifier
        """
        self._session_id = session_id

    def enable_tool_calling(self, enabled: bool = True) -> None:
        """
        Enable or disable tool calling functionality.

        Args:
            enabled: Whether to enable tool calling
        """
        self._tool_calling = enabled

    def generate_from_template(self, template: str, data: Dict[str, Any]) -> str:
        """
        Public method to generate text from a template with provided data.

        This is a convenience method that allows external callers to use the
        template replacement functionality without accessing the private method.

        Args:
            template: Text template containing parameters like {{param_name}}
            data: Dictionary with values to replace in the template

        Returns:
            Text with all template parameters replaced

        Example:
            >>> manager.generate_from_template(
            ...     "Hello {{name}}, your appointment is on {{date}} at {{time}}",
            ...     {"name": "John", "date": "Monday", "time": "3:00 PM"}
            ... )
            "Hello John, your appointment is on Monday at 3:00 PM"
        """
        return self._replace_template_params(template, data)


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Example configuration with template parameters
    config = {
        "system_prompt": "You are calling {{user_name}} at {{contact_number}} for their medical appointment.",
        "first_message": "Hello {{user_name}}, welcome to our clinic. How can I assist you today?",
        "language": "hi",
        "call_type": "Inbound call",
        "gender": "Female",
        "knowledge_bases": [{"name": "medical_kb", "path": "/path/to/kb"}],
        "handover_number": "+1234567890",
        "tool_calling": True,
    }

    # Mock agent config
    class MockAgentConfig:
        agent_name = "ClinicAssistant"

    # Mock user state with dynamic data
    class MockUserState:
        user_name = "John Doe"
        contact_number = "+919738301026"
        email = "john@example.com"

    # Create prompt manager
    prompt_manager = PromptManager(
        config=config,
        agent_config=MockAgentConfig(),
        session_id="test-session-123",
        tool_calling=True,
        logger=logger,
        user_state=MockUserState(),
    )

    # Generate system prompt (templates will be replaced automatically)
    system_prompt = prompt_manager._create_assistant_prompt()
    logger.info(f"System prompt length: {len(system_prompt)} characters")

    # Create context with tools
    context = prompt_manager._create_context_with_tools()
    if context:
        logger.info("Context created successfully with tools")

    # Get localized message
    message = prompt_manager.get_message("hi", "call_start")
    logger.info(f"Hindi call start message: {message}")

    # Example: Generate text from template with custom data
    template = "Hello {{name}}, your appointment is on {{date}} at {{time}} with Dr. {{doctor}}"
    custom_data = {
        "name": "Jane Smith",
        "date": "Monday, January 15",
        "time": "3:00 PM",
        "doctor": "Kumar",
    }
    result = prompt_manager.generate_from_template(template, custom_data)
    logger.info(f"Generated message: {result}")
