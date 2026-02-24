"""
Pydantic AI-Based Section Parser for Conversational Flow Extraction

This module uses Pydantic AI to extract structured conversation plans from system prompts.
Much simpler and cleaner than DSPY - direct Pydantic model outputs!

Core Principles (First Principles Design):
1. ConversationNode - Base atomic unit of conversation
2. Instruction - Meta-level directives (identity, style, guidelines)
3. Step - Sequential conversation progression
4. Question - Open-ended Q&A knowledge
5. Action - Agent behaviors (handover, end_call, search_docs)
6. Guardrail - Boundaries and restrictions
"""

import re
from typing import List, Dict, Any, Optional, Union, Literal
from pydantic import BaseModel, Field
from enum import Enum
from pydantic_ai import Agent


# =============================================================================
# Enums for Type Safety
# =============================================================================

class NodeType(str, Enum):
    """Types of conversation nodes"""
    INSTRUCTION = "Instruction"
    STEP = "Step"
    QUESTION = "Question"
    ACTION = "Action"
    GUARDRAIL = "Guardrail"


class InstructionType(str, Enum):
    """Types of instructions"""
    IDENTITY = "identity"  # Who the agent is
    STYLE = "style"  # How the agent communicates
    GUIDELINE = "guideline"  # Response rules
    SYSTEM = "system"  # System-level directives
    PERSONALITY = "personality"  # Agent personality traits
    TONE = "tone"  # Communication tone


class ActionType(str, Enum):
    """Types of actions"""
    HANDOVER = "handover"  # Transfer to human
    END_CALL = "end_call"  # Terminate conversation
    SEARCH_DOCS = "search_docs"  # Search knowledge base
    TRANSFER = "transfer"  # Transfer to another agent/department
    SCHEDULE = "schedule"  # Schedule a callback
    SEND_EMAIL = "send_email"  # Send email
    SEND_SMS = "send_sms"  # Send SMS


class FieldType(str, Enum):
    """Data types for fields"""
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ENUM = "enum"
    DATE = "date"
    EMAIL = "email"
    PHONE = "phone"
    URL = "url"


class RestrictionType(str, Enum):
    """Types of restrictions"""
    NEVER = "never"  # Must never do
    ALWAYS = "always"  # Must always do
    MUST = "must"  # Required to do
    MUST_NOT = "must_not"  # Prohibited from doing
    SHOULD = "should"  # Recommended
    SHOULD_NOT = "should_not"  # Discouraged


# =============================================================================
# Pydantic Models (First Principles Schema)
# =============================================================================

class BaseNode(BaseModel):
    """Base node with schema.org-like structure"""
    id: str = Field(description="Unique identifier")
    name: str = Field(description="Human-readable name")
    content: str = Field(description="Main content/text")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        use_enum_values = True


# -----------------------------------------------------------------------------
# Instruction Models
# -----------------------------------------------------------------------------

class InstructionModel(BaseNode):
    """
    Meta-level instruction for the agent.

    Schema.org equivalent: CreativeWork/instructions
    """
    type: InstructionType = Field(
        description="Type of instruction: identity, style, guideline, system, personality, tone"
    )
    priority: int = Field(
        default=0,
        description="Priority level (higher = more important)"
    )
    applies_to: List[str] = Field(
        default_factory=list,
        description="List of step IDs this instruction applies to (empty = all)"
    )
    examples: List[str] = Field(
        default_factory=list,
        description="Example phrases or behaviors"
    )


# -----------------------------------------------------------------------------
# Step Models
# -----------------------------------------------------------------------------

class FieldSchema(BaseModel):
    """
    Schema for a data field to collect.

    Schema.org equivalent: Property
    """
    name: str = Field(description="Field name (snake_case)")
    field_type: FieldType = Field(description="Data type")
    description: str = Field(description="What this field represents")
    required: bool = Field(default=True, description="Is this field required?")
    enum_values: Optional[List[str]] = Field(
        default=None,
        description="Possible values for enum fields"
    )
    validation_pattern: Optional[str] = Field(
        default=None,
        description="Regex pattern for validation"
    )
    default_value: Optional[Any] = Field(
        default=None,
        description="Default value if not provided"
    )
    prompt_text: Optional[str] = Field(
        default=None,
        description="Exact text to use when prompting for this field"
    )

    class Config:
        use_enum_values = True


class ConditionalBranch(BaseModel):
    """
    Conditional branching logic.

    Schema.org equivalent: Action/potentialAction
    """
    condition: str = Field(description="Condition to evaluate (e.g., 'yes', 'no', 'interested')")
    target_step_id: Optional[str] = Field(
        default=None,
        description="ID of step to jump to if condition is true"
    )
    condition_type: Literal["yes_no", "multiple_choice", "expression"] = Field(
        default="yes_no",
        description="Type of condition"
    )


class StepModel(BaseNode):
    """
    Sequential conversation step.

    Schema.org equivalent: HowToStep
    """
    order: int = Field(description="Order in the conversation sequence")
    type: Literal["greeting", "question", "pitch", "closing", "confirmation"] = Field(
        default="question",
        description="Type of step"
    )
    fields: List[FieldSchema] = Field(
        default_factory=list,
        description="Data fields to collect in this step"
    )
    next_step_id: Optional[str] = Field(
        default=None,
        description="ID of the next step (None = end)"
    )
    conditional_branches: List[ConditionalBranch] = Field(
        default_factory=list,
        description="Conditional branches from this step"
    )
    prompt_template: str = Field(
        default="",
        description="Template for prompting user (supports {{field}} placeholders)"
    )
    validation_rules: List[str] = Field(
        default_factory=list,
        description="Validation rules for this step"
    )
    retry_prompts: List[str] = Field(
        default_factory=list,
        description="Prompts to use if user response is invalid"
    )
    max_retries: int = Field(
        default=3,
        description="Maximum retry attempts"
    )
    skip_conditions: List[str] = Field(
        default_factory=list,
        description="Conditions under which to skip this step"
    )


# -----------------------------------------------------------------------------
# Question Models (FAQ)
# -----------------------------------------------------------------------------

class QuestionModel(BaseNode):
    """
    Open-ended Q&A knowledge.

    Schema.org equivalent: Question with acceptedAnswer
    """
    question_text: str = Field(description="The question text")
    answer_text: str = Field(description="The answer text")
    keywords: List[str] = Field(
        default_factory=list,
        description="Keywords to match this Q&A"
    )
    category: Optional[str] = Field(
        default=None,
        description="Category/topic of this Q&A"
    )
    related_questions: List[str] = Field(
        default_factory=list,
        description="IDs of related questions"
    )
    confidence_threshold: float = Field(
        default=0.7,
        description="Minimum confidence to use this answer"
    )
    follow_up_questions: List[str] = Field(
        default_factory=list,
        description="Suggested follow-up questions"
    )


# -----------------------------------------------------------------------------
# Action Models
# -----------------------------------------------------------------------------

class ActionTrigger(BaseModel):
    """
    Condition that triggers an action.

    Schema.org equivalent: Action/actionStatus
    """
    condition_type: Literal["keyword", "sentiment", "intent", "explicit", "time", "count"] = Field(
        description="Type of trigger condition"
    )
    condition_value: Union[str, List[str], int, float] = Field(
        description="Value to match (keyword, sentiment score, etc.)"
    )
    operator: Literal["equals", "contains", "greater_than", "less_than", "matches_regex"] = Field(
        default="equals",
        description="Comparison operator"
    )


class ActionModel(BaseNode):
    """
    Agent action to take.

    Schema.org equivalent: Action
    """
    type: ActionType = Field(description="Type of action")
    triggers: List[ActionTrigger] = Field(
        default_factory=list,
        description="Conditions that trigger this action"
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Parameters for the action"
    )
    priority: int = Field(
        default=0,
        description="Priority (higher = more important)"
    )
    requires_confirmation: bool = Field(
        default=False,
        description="Does this action require user confirmation?"
    )
    confirmation_prompt: Optional[str] = Field(
        default=None,
        description="Prompt to show when confirming"
    )
    success_message: Optional[str] = Field(
        default=None,
        description="Message to show on success"
    )
    failure_message: Optional[str] = Field(
        default=None,
        description="Message to show on failure"
    )

    class Config:
        use_enum_values = True


# -----------------------------------------------------------------------------
# Guardrail Models
# -----------------------------------------------------------------------------

class GuardrailModel(BaseNode):
    """
    Boundary or restriction.

    Schema.org equivalent: Constraint
    """
    type: RestrictionType = Field(
        description="Type of restriction: never, always, must, must_not, should, should_not"
    )
    rule: str = Field(description="The rule text")
    enforcement_level: Literal["strict", "warning", "soft"] = Field(
        default="strict",
        description="How strictly to enforce"
    )
    applies_to: List[str] = Field(
        default_factory=list,
        description="Step IDs this applies to (empty = all)"
    )
    violation_message: Optional[str] = Field(
        default=None,
        description="Message to show on violation"
    )
    examples: List[str] = Field(
        default_factory=list,
        description="Example violations"
    )

    class Config:
        use_enum_values = True


# =============================================================================
# Conversation Plan Model
# =============================================================================

class ConversationPlan(BaseModel):
    """
    Complete conversation plan.

    Schema.org equivalent: HowTo - a complete instruction set
    """
    instructions: List[InstructionModel] = Field(
        default_factory=list,
        description="Meta-level instructions for the agent (identity, style, guidelines)"
    )
    steps: List[StepModel] = Field(
        default_factory=list,
        description="Sequential conversation steps in order"
    )
    questions: List[QuestionModel] = Field(
        default_factory=list,
        description="Open-ended Q&A knowledge base (FAQs)"
    )
    actions: List[ActionModel] = Field(
        default_factory=list,
        description="Agent actions (handover, end_call, search_docs, etc.)"
    )
    guardrails: List[GuardrailModel] = Field(
        default_factory=list,
        description="Restrictions and boundaries"
    )

    # Computed properties
    @property
    def nodes_by_id(self) -> Dict[str, BaseNode]:
        """Get all nodes indexed by ID"""
        result = {}
        for node_list in [self.instructions, self.steps, self.questions, self.actions, self.guardrails]:
            for node in node_list:
                result[node.id] = node
        return result

    @property
    def steps_by_order(self) -> Dict[int, StepModel]:
        """Get steps indexed by order"""
        return {step.order: step for step in self.steps}

    def get_node(self, node_id: str) -> Optional[BaseNode]:
        """Get node by ID"""
        return self.nodes_by_id.get(node_id)

    def get_step(self, order: int) -> Optional[StepModel]:
        """Get step by order"""
        return self.steps_by_order.get(order)

    def get_first_step(self) -> Optional[StepModel]:
        """Get the first step in the conversation"""
        if not self.steps:
            return None
        return min(self.steps, key=lambda s: s.order)

    class Config:
        use_enum_values = True


# =============================================================================
# Pydantic AI Agents
# =============================================================================

# System prompts for extraction agents
EXTRACTION_SYSTEM_PROMPT = """You are an expert at analyzing conversational AI system prompts and extracting structured information.

Your task is to parse a system prompt and extract all relevant information into a structured format.

The system prompt may contain:
1. **Instructions** - Identity, style, guidelines, system directives (meta-level, not active in conversation)
2. **Steps** - Sequential conversation flow with data collection fields
3. **Questions** - FAQs that can be answered anytime
4. **Actions** - Agent behaviors like handover, end_call, search_docs
5. **Guardrails** - Restrictions and boundaries

Extract ALL details, preserving exact phrasing, examples, and context.
"""


# Create the main extraction agent
# Use gpt-4o-mini for faster parsing (128K context, 2-5x faster than gpt-4o)
# Falls back to gpt-4o if you need more complex reasoning
# conversation_plan_agent = Agent(
#     'openai:gpt-5.2-mini',
#     output_type=ConversationPlan,
#     system_prompt=EXTRACTION_SYSTEM_PROMPT
# )


# =============================================================================
# Main Parsing Function
# =============================================================================
#
# from openai import AsyncOpenAI
# from typing import Optional
# import time
# import json
# client = AsyncOpenAI()
#
# async def parse_conversation_plan_async(
#     system_prompt: str,
#     model: str = "gpt-4o-mini",
#     api_key: Optional[str] = None
# ) -> ConversationPlan:
#     """
#     Ultra-fast version using raw OpenAI API (skips pydantic-ai).
#     2–5× faster due to removing JSON type repair + extra validation steps.
#     """
#     import logging
#     logger = logging.getLogger(__name__)
#
#     total_start = time.time()
#     print("normalizing prompt")
#
#     # STEP 1: normalize system prompt
#     normalized_prompt = _normalize_prompt(system_prompt)
#
#     print(f"Calling {model} using fast raw JSON mode...")
#
#     api_start = time.time()
#
#     resp = await client.chat.completions.create(
#         model=model,
#         messages=[
#             {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
#             {"role": "user", "content": normalized_prompt}
#         ],
#         response_format={"type": "json_object"},
#         api_key=api_key
#     )
#
#     api_duration = time.time() - api_start
#     print(f"⏱️ OpenAI call finished in {api_duration:.2f}s")
#
#     # STEP 3: Extract JSON string
#     content = resp.choices[0].message.content
#
#     # STEP 4: Parse with Pydantic (fast validation)
#     try:
#         plan = ConversationPlan.model_validate_json(content)
#     except Exception as e:
#         print("❌ JSON validation failed. Dumping raw:", content)
#         raise e
#
#     # STEP 5: Post-process step linking
#     _link_steps(plan.steps)
#
#     total_duration = time.time() - total_start
#     print(f"✅ Total parse_conversation_plan_async: {total_duration:.2f}s")
#
#     return plan
#
async def parse_conversation_plan_async(
    system_prompt: str,
    model: str = 'openai:gpt-4o-mini',
    api_key: Optional[str] = None
) -> ConversationPlan:
    """
    Parse a system prompt into a structured ConversationPlan (async version).

    This uses Pydantic AI to extract structured information directly into Pydantic models.
    Use this version when calling from async contexts.

    Args:
        system_prompt: Raw system prompt text
        model: Model to use (default: openai:gpt-4o-mini, 2-5x faster than gpt-4o)
        api_key: Optional API key (uses env var if not provided)

    Returns:
        ConversationPlan with extracted components (all details preserved)

    Example:
        >>> plan = await parse_conversation_plan_async(my_prompt)
        >>> print(f"Found {len(plan.steps)} steps")
    """
    import time

    total_start = time.time()
    print("normalizing prompt")
    # Normalize prompt
    normalized_prompt = _normalize_prompt(system_prompt)

    print("creating model for conversation plan...")
    # Create agent (use custom model/key if provided)
    if model != 'openai:gpt-4o' or api_key:
        agent = Agent(
            model,
            output_type=ConversationPlan,
            system_prompt=EXTRACTION_SYSTEM_PROMPT
        )
    else:
        agent = conversation_plan_agent

    # Run extraction (async) - this is the slow part
    print(f"🤖 Calling {model} API to parse conversation plan...")
    api_start = time.time()
    result = await agent.run(normalized_prompt)
    api_duration = time.time() - api_start
    print(f"⏱️ {model} API call completed in {api_duration:.2f}s")

    # Post-process: link steps
    plan = result.output
    _link_steps(plan.steps)

    total_duration = time.time() - total_start
    print(f"✅ Total parse_conversation_plan_async: {total_duration:.2f}s")

    return plan
#

def parse_conversation_plan(
    system_prompt: str,
    model: str = 'groq:mixtral-8x7b',
    api_key: Optional[str] = None
) -> ConversationPlan:
    """
    Parse a system prompt into a structured ConversationPlan (sync version).

    This uses Pydantic AI to extract structured information directly into Pydantic models.

    NOTE: If you're calling this from an async function, use `parse_conversation_plan_async` instead
    to avoid "event loop already running" errors.

    Args:
        system_prompt: Raw system prompt text
        model: Model to use (default: openai:gpt-4o-mini, 2-5x faster than gpt-4o)
        api_key: Optional API key (uses env var if not provided)

    Returns:
        ConversationPlan with extracted components (all details preserved)

    Example:
        >>> plan = parse_conversation_plan(my_prompt)
        >>> print(f"Found {len(plan.steps)} steps")
        >>> print(f"Found {len(plan.questions)} FAQs")
        >>>
        >>> # Access first step
        >>> first_step = plan.get_first_step()
        >>> print(f"First step: {first_step.name}")
        >>> print(f"Fields to collect: {[f.name for f in first_step.fields]}")
    """
    import asyncio

    # Check if we're in an async context
    try:
        _ = asyncio.get_running_loop()
        # We're in an async context - raise a helpful error
        raise RuntimeError(
            "parse_conversation_plan() cannot be called from an async context. "
            "Use 'await parse_conversation_plan_async()' instead."
        )
    except RuntimeError as e:
        # Check if the error is from get_running_loop (no event loop)
        # vs our custom error (already in async context)
        if "no running event loop" in str(e).lower() or "there is no current event loop" in str(e).lower():
            # Not in async context, proceed with sync version
            pass
        else:
            # Re-raise the helpful error message
            raise

    # Normalize prompt
    normalized_prompt = _normalize_prompt(system_prompt)

    # Create agent (use custom model/key if provided)
    if model != 'openai:gpt-4o' or api_key:
        agent = Agent(
            model,
            output_type=ConversationPlan,
            system_prompt=EXTRACTION_SYSTEM_PROMPT
        )
    else:
        agent = conversation_plan_agent

    # Run extraction
    result = agent.run_sync(normalized_prompt)

    # Post-process: link steps
    plan = result.output
    _link_steps(plan.steps)

    return plan


def _normalize_prompt(text: str) -> str:
    """Normalize whitespace and line breaks"""
    # Handle literal escaped newlines
    text = text.replace('\\\\r\\\\n', '\n')
    text = text.replace('\\\\n', '\n')
    text = re.sub(r'\r\n', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def _link_steps(steps: List[StepModel]):
    """Link steps with next_step_id"""
    # Sort by order
    steps.sort(key=lambda s: s.order)

    # Link sequential steps (only if no conditional branches)
    for i in range(len(steps) - 1):
        if not steps[i].conditional_branches and not steps[i].next_step_id:
            steps[i].next_step_id = steps[i + 1].id


# =============================================================================
# Convenience Functions
# =============================================================================

def conversation_plan_to_json(plan: ConversationPlan) -> str:
    """
    Convert ConversationPlan to JSON string.

    Args:
        plan: ConversationPlan to convert

    Returns:
        JSON string representation
    """
    return plan.model_dump_json(indent=2)


def conversation_plan_to_dict(plan: ConversationPlan) -> Dict[str, Any]:
    """
    Convert ConversationPlan to dictionary.

    Args:
        plan: ConversationPlan to convert

    Returns:
        Dictionary representation
    """
    return plan.model_dump()


# =============================================================================
# Migration Helper (from old SectionParser)
# =============================================================================

def migrate_from_old_parser(
    old_parsed_config,
    model: str = 'openai:gpt-4',
    api_key: Optional[str] = None
) -> ConversationPlan:
    """
    Migrate from old SectionParser ParsedFlowConfig to new ConversationPlan.

    This helper allows gradual migration from the old parser.

    Args:
        old_parsed_config: ParsedFlowConfig from old SectionParser
        model: Model to use for re-parsing
        api_key: Optional API key

    Returns:
        New ConversationPlan
    """
    # If we have the original prompt, re-parse for best results
    if hasattr(old_parsed_config, 'raw_prompt'):
        return parse_conversation_plan(
            old_parsed_config.raw_prompt,
            model=model,
            api_key=api_key
        )

    # Otherwise, map old structure to new
    instructions = []
    steps = []
    questions = []
    actions = []
    guardrails = []

    # Map identity -> instruction
    if hasattr(old_parsed_config, 'identity') and old_parsed_config.identity:
        instructions.append(
            InstructionModel(
                id=old_parsed_config.identity.id,
                name=old_parsed_config.identity.section_name,
                content=old_parsed_config.identity.content,
                instruction_type=InstructionType.IDENTITY
            )
        )

    # Map instructions -> instruction
    if hasattr(old_parsed_config, 'instructions') and old_parsed_config.instructions:
        instructions.append(
            InstructionModel(
                id=old_parsed_config.instructions.id,
                name=old_parsed_config.instructions.section_name,
                content=old_parsed_config.instructions.content,
                instruction_type=InstructionType.SYSTEM
            )
        )

    # Map guidelines -> instructions
    if hasattr(old_parsed_config, 'guidelines'):
        for guideline in old_parsed_config.guidelines:
            instructions.append(
                InstructionModel(
                    id=guideline.id,
                    name=guideline.section_name,
                    content=guideline.content,
                    instruction_type=InstructionType.GUIDELINE
                )
            )

    # Map questions -> steps
    if hasattr(old_parsed_config, 'questions'):
        for idx, question in enumerate(old_parsed_config.questions):
            fields = [
                FieldSchema(
                    name=field_name,
                    field_type=FieldType(question.field_types.get(field_name, "string")),
                    description=question.field_descriptions.get(field_name, field_name),
                    required=True
                )
                for field_name in question.required
            ]

            steps.append(
                StepModel(
                    id=question.id,
                    name=question.section_name,
                    content=question.content,
                    order=idx,
                    step_type="question",
                    fields=fields,
                    next_step_id=question.next_section_id,
                    prompt_template=question.content
                )
            )

    # Map FAQs -> questions
    if hasattr(old_parsed_config, 'faqs'):
        for faq in old_parsed_config.faqs:
            questions.append(
                QuestionModel(
                    id=faq.id,
                    name=faq.section_name,
                    content=faq.content,
                    question_text=faq.section_name,
                    answer_text=faq.content
                )
            )

    return ConversationPlan(
        instructions=instructions,
        steps=steps,
        questions=questions,
        actions=actions,
        guardrails=guardrails
    )


# =============================================================================
# Example Usage
# =============================================================================

if __name__ == "__main__":
    print("Pydantic AI Section Parser")
    print("=" * 50)
    print()
    print("This module provides:")
    print("✓ Type-safe Pydantic models for all components")
    print("✓ Pydantic AI for direct structured extraction")
    print("✓ No manual JSON parsing needed")
    print("✓ Preserves all details from system prompts")
    print()
    print("Core Components:")
    print("- InstructionModel: Identity, style, guidelines")
    print("- StepModel: Sequential conversation steps")
    print("- QuestionModel: Open-ended Q&A (FAQs)")
    print("- ActionModel: Agent actions (handover, search, etc.)")
    print("- GuardrailModel: Restrictions and boundaries")
    print()
    print("Usage:")
    print(">>> plan = parse_conversation_plan(system_prompt)")
    print(">>> print(plan.model_dump_json(indent=2))")
    print()
    print("Module loaded successfully!")
