"""
DSPY-Based Section Parser for Conversational Flow Extraction

This module uses DSPY with Pydantic models to extract structured conversation plans
from system prompts without losing any details.

Core Principles (First Principles Design):
1. ConversationNode - Base atomic unit of conversation
2. Instruction - Meta-level directives (identity, style, guidelines)
3. Step - Sequential conversation progression
4. Question - Open-ended Q&A knowledge
5. Action - Agent behaviors (handover, end_call, search_docs)
6. Guardrail - Boundaries and restrictions

DSPY Integration:
- Uses Pydantic models directly as output fields
- No manual JSON parsing needed
- Type-safe and preserves all details
"""

import re
from typing import List, Dict, Any, Optional, Union, Literal
from pydantic import BaseModel, Field
from enum import Enum
import dspy


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
    instruction_type: InstructionType = Field(
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
    step_type: Literal["greeting", "question", "pitch", "closing", "confirmation"] = Field(
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
    action_type: ActionType = Field(description="Type of action")
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
    restriction_type: RestrictionType = Field(
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
        description="Meta-level instructions"
    )
    steps: List[StepModel] = Field(
        default_factory=list,
        description="Sequential conversation steps"
    )
    questions: List[QuestionModel] = Field(
        default_factory=list,
        description="Open-ended Q&A knowledge"
    )
    actions: List[ActionModel] = Field(
        default_factory=list,
        description="Agent actions"
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
# DSPY Signatures (Using Pydantic Models)
# =============================================================================

class ExtractInstructions(dspy.Signature):
    """
    Extract meta-level instructions from system prompt.

    Instructions include:
    - Identity: Who the agent is (role, personality)
    - Style: How to communicate (tone, language)
    - Guidelines: Response rules and best practices
    - System: Technical directives
    - Personality: Personality traits
    - Tone: Communication tone

    Extract ALL details, including:
    - Exact phrasing
    - Examples provided
    - Priorities
    - Context and nuances
    """
    system_prompt = dspy.InputField(desc="Full system prompt text")
    extracted_instructions = dspy.OutputField(desc="JSON array of instructions with fields: id (str), name (str), content (str), instruction_type (identity/style/guideline/system/personality/tone), priority (int), applies_to (list), examples (list), metadata (dict)")


class ExtractConversationSteps(dspy.Signature):
    """
    Extract ordered conversation steps.

    Steps are sequential and form the main conversation flow.
    Each step may collect data fields.

    Extract ALL details for each step:
    - Exact prompt templates
    - All fields with their types and descriptions
    - Validation rules
    - Retry logic
    - Skip conditions
    - Order and dependencies
    """
    system_prompt = dspy.InputField(desc="Full system prompt text")
    steps = dspy.OutputField(desc="JSON array of steps with fields: id, name, content, order (int), step_type (greeting/question/pitch/closing/confirmation), fields (array of field objects), next_step_id, conditional_branches (array), prompt_template, validation_rules (array), retry_prompts (array), max_retries (int), skip_conditions (array), metadata")


class ExtractConditionalBranches(dspy.Signature):
    """
    Extract conditional branching logic from a step.

    Identifies YES/NO branches, multi-choice branches, etc.
    Preserves exact conditions and targets.
    """
    step_content = dspy.InputField(desc="Step content to analyze for branches")
    all_step_names = dspy.InputField(desc="Comma-separated list of all step names for reference")
    branches = dspy.OutputField(desc="JSON array of branches with fields: condition (str), target_step_id (str), condition_type (yes_no/multiple_choice/expression)")


class ExtractQuestions(dspy.Signature):
    """
    Extract open-ended Q&A pairs (FAQs).

    These can be answered in any order during the conversation.

    Extract ALL details:
    - Exact question and answer text
    - Keywords and variations
    - Categories
    - Related questions
    - Follow-ups
    """
    system_prompt = dspy.InputField(desc="Full system prompt text")
    questions = dspy.OutputField(desc="JSON array of Q&A with fields: id, name, content, question_text, answer_text, keywords (array), category, related_questions (array), confidence_threshold (float), follow_up_questions (array), metadata")


class ExtractActions(dspy.Signature):
    """
    Extract agent actions.

    Actions include:
    - Handover: Transfer to human agent
    - End Call: Terminate conversation
    - Search Docs: Query knowledge base
    - Transfer: Move to another agent/department
    - Schedule: Schedule a callback
    - Send Email/SMS: Communication actions

    Extract ALL details:
    - Exact triggers (keywords, sentiment, intent)
    - Parameters
    - Confirmation requirements
    - Success/failure messages
    """
    system_prompt = dspy.InputField(desc="Full system prompt text")
    actions = dspy.OutputField(desc="JSON array of actions with fields: id, name, content, action_type (handover/end_call/search_docs/transfer/schedule/send_email/send_sms), triggers (array of trigger objects), parameters (dict), priority (int), requires_confirmation (bool), confirmation_prompt, success_message, failure_message, metadata")


class ExtractGuardrails(dspy.Signature):
    """
    Extract restrictions and boundaries.

    Guardrails prevent the agent from crossing certain boundaries.

    Extract ALL details:
    - Exact rule text
    - Restriction type (never, always, must, must_not)
    - Enforcement level
    - Examples of violations
    - Violation messages
    """
    system_prompt = dspy.InputField(desc="Full system prompt text")
    guardrails = dspy.OutputField(desc="JSON array of guardrails with fields: id, name, content, restriction_type (never/always/must/must_not/should/should_not), rule, enforcement_level (strict/warning/soft), applies_to (array), violation_message, examples (array), metadata")


# =============================================================================
# DSPY Modules
# =============================================================================

class InstructionExtractor(dspy.Module):
    """Module to extract instructions using DSPY"""

    def __init__(self):
        super().__init__()
        self.extract = dspy.ChainOfThought(ExtractInstructions)

    def forward(self, system_prompt: str) -> List[InstructionModel]:
        """Extract instructions from prompt"""
        result = self.extract(system_prompt=system_prompt)

        # Parse JSON string to Pydantic models
        import json
        try:
            instructions_data = json.loads(result.extracted_instructions)
            instructions = []
            for idx, data in enumerate(instructions_data):
                try:
                    inst = InstructionModel(
                        id=data.get("id", f"instruction_{idx}"),
                        name=data.get("name", f"Instruction {idx}"),
                        content=data.get("content", ""),
                        instruction_type=InstructionType(data.get("instruction_type", "system")),
                        priority=data.get("priority", 0),
                        applies_to=data.get("applies_to", []),
                        examples=data.get("examples", []),
                        metadata=data.get("metadata", {})
                    )
                    instructions.append(inst)
                except Exception:
                    # Skip invalid entries
                    pass
            return instructions
        except (json.JSONDecodeError, TypeError):
            return []


class StepExtractor(dspy.Module):
    """Module to extract conversation steps"""

    def __init__(self):
        super().__init__()
        self.extract = dspy.ChainOfThought(ExtractConversationSteps)
        self.extract_branches = dspy.ChainOfThought(ExtractConditionalBranches)

    def forward(self, system_prompt: str) -> List[StepModel]:
        """Extract steps from prompt"""
        import json
        result = self.extract(system_prompt=system_prompt)

        # Parse JSON string to Step models
        try:
            steps_data = json.loads(result.steps)
            steps = []
            for data in steps_data:
                try:
                    # Parse fields
                    fields = []
                    for f_data in data.get("fields", []):
                        field = FieldSchema(
                            name=f_data.get("name", ""),
                            field_type=FieldType(f_data.get("field_type", "string")),
                            description=f_data.get("description", ""),
                            required=f_data.get("required", True),
                            enum_values=f_data.get("enum_values"),
                            validation_pattern=f_data.get("validation_pattern"),
                            default_value=f_data.get("default_value"),
                            prompt_text=f_data.get("prompt_text")
                        )
                        fields.append(field)

                    # Parse branches (will be updated later)
                    branches = []
                    for b_data in data.get("conditional_branches", []):
                        branch = ConditionalBranch(
                            condition=b_data.get("condition", ""),
                            target_step_id=b_data.get("target_step_id"),
                            condition_type=b_data.get("condition_type", "yes_no")
                        )
                        branches.append(branch)

                    step = StepModel(
                        id=data.get("id", f"step_{data.get('order', 0)}"),
                        name=data.get("name", f"Step {data.get('order', 0)}"),
                        content=data.get("content", ""),
                        order=data.get("order", 0),
                        step_type=data.get("step_type", "question"),
                        fields=fields,
                        next_step_id=data.get("next_step_id"),
                        conditional_branches=branches,
                        prompt_template=data.get("prompt_template", ""),
                        validation_rules=data.get("validation_rules", []),
                        retry_prompts=data.get("retry_prompts", []),
                        max_retries=data.get("max_retries", 3),
                        skip_conditions=data.get("skip_conditions", []),
                        metadata=data.get("metadata", {})
                    )
                    steps.append(step)
                except Exception:
                    pass
        except (json.JSONDecodeError, TypeError):
            steps = []

        # Link steps
        self._link_steps(steps)

        return steps

    def _link_steps(self, steps: List[StepModel]):
        """Link steps with next_step_id"""
        # Sort by order
        steps.sort(key=lambda s: s.order)

        # Link sequential steps (only if no conditional branches)
        for i in range(len(steps) - 1):
            if not steps[i].conditional_branches and not steps[i].next_step_id:
                steps[i].next_step_id = steps[i + 1].id


class QuestionExtractor(dspy.Module):
    """Module to extract Q&A pairs"""

    def __init__(self):
        super().__init__()
        self.extract = dspy.ChainOfThought(ExtractQuestions)

    def forward(self, system_prompt: str) -> List[QuestionModel]:
        """Extract questions from prompt"""
        import json
        result = self.extract(system_prompt=system_prompt)

        try:
            questions_data = json.loads(result.questions)
            questions = []
            for idx, data in enumerate(questions_data):
                try:
                    q = QuestionModel(
                        id=data.get("id", f"question_{idx}"),
                        name=data.get("name", "")[:50],
                        content=data.get("content", data.get("answer_text", "")),
                        question_text=data.get("question_text", ""),
                        answer_text=data.get("answer_text", ""),
                        keywords=data.get("keywords", []),
                        category=data.get("category"),
                        related_questions=data.get("related_questions", []),
                        confidence_threshold=data.get("confidence_threshold", 0.7),
                        follow_up_questions=data.get("follow_up_questions", []),
                        metadata=data.get("metadata", {})
                    )
                    questions.append(q)
                except Exception:
                    pass
            return questions
        except (json.JSONDecodeError, TypeError):
            return []


class ActionExtractor(dspy.Module):
    """Module to extract actions"""

    def __init__(self):
        super().__init__()
        self.extract = dspy.ChainOfThought(ExtractActions)

    def forward(self, system_prompt: str) -> List[ActionModel]:
        """Extract actions from prompt"""
        import json
        result = self.extract(system_prompt=system_prompt)

        try:
            actions_data = json.loads(result.actions)
            actions = []
            for idx, data in enumerate(actions_data):
                try:
                    # Parse triggers
                    triggers = []
                    for t_data in data.get("triggers", []):
                        trigger = ActionTrigger(
                            condition_type=t_data.get("condition_type", "keyword"),
                            condition_value=t_data.get("condition_value", ""),
                            operator=t_data.get("operator", "equals")
                        )
                        triggers.append(trigger)

                    action = ActionModel(
                        id=data.get("id", f"action_{idx}"),
                        name=data.get("name", f"Action {idx}"),
                        content=data.get("content", data.get("name", "")),
                        action_type=ActionType(data.get("action_type", "handover")),
                        triggers=triggers,
                        parameters=data.get("parameters", {}),
                        priority=data.get("priority", 0),
                        requires_confirmation=data.get("requires_confirmation", False),
                        confirmation_prompt=data.get("confirmation_prompt"),
                        success_message=data.get("success_message"),
                        failure_message=data.get("failure_message"),
                        metadata=data.get("metadata", {})
                    )
                    actions.append(action)
                except Exception:
                    pass
            return actions
        except (json.JSONDecodeError, TypeError):
            return []


class GuardrailExtractor(dspy.Module):
    """Module to extract guardrails"""

    def __init__(self):
        super().__init__()
        self.extract = dspy.ChainOfThought(ExtractGuardrails)

    def forward(self, system_prompt: str) -> List[GuardrailModel]:
        """Extract guardrails from prompt"""
        import json
        result = self.extract(system_prompt=system_prompt)

        try:
            guardrails_data = json.loads(result.guardrails)
            guardrails = []
            for idx, data in enumerate(guardrails_data):
                try:
                    g = GuardrailModel(
                        id=data.get("id", f"guardrail_{idx}"),
                        name=data.get("name", f"Guardrail {idx}"),
                        content=data.get("content", data.get("rule", "")),
                        restriction_type=RestrictionType(data.get("restriction_type", "must_not")),
                        rule=data.get("rule", ""),
                        enforcement_level=data.get("enforcement_level", "strict"),
                        applies_to=data.get("applies_to", []),
                        violation_message=data.get("violation_message"),
                        examples=data.get("examples", []),
                        metadata=data.get("metadata", {})
                    )
                    guardrails.append(g)
                except Exception:
                    pass
            return guardrails
        except (json.JSONDecodeError, TypeError):
            return []


class ConversationPlanExtractor(dspy.Module):
    """
    Main module to extract complete conversation plan.

    This is the primary interface for parsing system prompts.
    Uses DSPY with Pydantic models to preserve all details.
    """

    def __init__(self):
        super().__init__()
        self.instruction_extractor = InstructionExtractor()
        self.step_extractor = StepExtractor()
        self.question_extractor = QuestionExtractor()
        self.action_extractor = ActionExtractor()
        self.guardrail_extractor = GuardrailExtractor()

    def forward(self, system_prompt: str) -> ConversationPlan:
        """
        Extract conversation plan from system prompt.

        Args:
            system_prompt: Raw system prompt text

        Returns:
            ConversationPlan with all extracted components (no details lost)
        """
        # Normalize prompt
        normalized_prompt = self._normalize_prompt(system_prompt)

        # Extract all components in parallel (DSPY handles batching)
        instructions = self.instruction_extractor(system_prompt=normalized_prompt)
        steps = self.step_extractor(system_prompt=normalized_prompt)
        questions = self.question_extractor(system_prompt=normalized_prompt)
        actions = self.action_extractor(system_prompt=normalized_prompt)
        guardrails = self.guardrail_extractor(system_prompt=normalized_prompt)

        # Build and return plan
        plan = ConversationPlan(
            instructions=instructions,
            steps=steps,
            questions=questions,
            actions=actions,
            guardrails=guardrails
        )

        return plan

    def _normalize_prompt(self, text: str) -> str:
        """Normalize whitespace and line breaks"""
        # Handle literal escaped newlines
        text = text.replace('\\\\r\\\\n', '\n')
        text = text.replace('\\\\n', '\n')
        text = re.sub(r'\r\n', '\n', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()


# =============================================================================
# Convenience Functions
# =============================================================================

def parse_conversation_plan(
    system_prompt: str,
    lm: Optional[dspy.LM] = None
) -> ConversationPlan:
    """
    Convenience function to parse a system prompt.

    Args:
        system_prompt: Raw system prompt text
        lm: Optional language model to use (defaults to dspy configured LM)

    Returns:
        ConversationPlan with extracted components (all details preserved)

    Example:
        >>> import dspy
        >>> lm = dspy.OpenAI(model="gpt-4")
        >>> dspy.settings.configure(lm=lm)
        >>>
        >>> plan = parse_conversation_plan(my_prompt)
        >>> print(f"Found {len(plan.steps)} steps")
        >>> print(f"Found {len(plan.questions)} FAQs")
        >>>
        >>> # Access first step
        >>> first_step = plan.get_first_step()
        >>> print(f"First step: {first_step.name}")
        >>> print(f"Fields to collect: {[f.name for f in first_step.fields]}")
    """
    if lm:
        with dspy.context(lm=lm):
            extractor = ConversationPlanExtractor()
            return extractor(system_prompt=system_prompt)
    else:
        extractor = ConversationPlanExtractor()
        return extractor(system_prompt=system_prompt)


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
    lm: Optional[dspy.LM] = None
) -> ConversationPlan:
    """
    Migrate from old SectionParser ParsedFlowConfig to new ConversationPlan.

    This helper allows gradual migration from the old parser.

    Args:
        old_parsed_config: ParsedFlowConfig from old SectionParser
        lm: Optional LM for re-parsing with DSPY

    Returns:
        New ConversationPlan
    """
    # If we have LM, re-parse for best results
    if lm and hasattr(old_parsed_config, 'raw_prompt'):
        return parse_conversation_plan(old_parsed_config.raw_prompt, lm=lm)

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
            # Try to split content into Q&A
            content = faq.content
            q_text = faq.section_name
            a_text = content

            questions.append(
                QuestionModel(
                    id=faq.id,
                    name=faq.section_name,
                    content=content,
                    question_text=q_text,
                    answer_text=a_text
                )
            )

    # Map objections -> actions (special case)
    if hasattr(old_parsed_config, 'objections'):
        for objection in old_parsed_config.objections:
            triggers = [
                ActionTrigger(
                    condition_type="keyword",
                    condition_value=keyword,
                    operator="contains"
                )
                for keyword in objection.trigger_keywords
            ]

            # Objections are handled as special steps or actions
            # Let's add them as both for flexibility
            actions.append(
                ActionModel(
                    id=objection.id,
                    name=objection.section_name,
                    content=objection.content,
                    action_type=ActionType.HANDOVER,  # Or custom handling
                    triggers=triggers,
                    metadata={"type": "objection_handler"}
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
    print("DSPY Section Parser with Pydantic Models")
    print("=" * 50)
    print()
    print("This module provides:")
    print("✓ Type-safe Pydantic models for all components")
    print("✓ DSPY signatures using actual model classes")
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
    print(">>> import dspy")
    print(">>> lm = dspy.OpenAI(model='gpt-4')")
    print(">>> dspy.settings.configure(lm=lm)")
    print(">>> plan = parse_conversation_plan(system_prompt)")
    print(">>> print(plan.model_dump_json(indent=2))")
    print()
    print("Module loaded successfully!")
