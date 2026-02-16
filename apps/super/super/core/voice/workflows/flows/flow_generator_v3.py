"""
Flow Generator V3 - DSPy-Enhanced Node Generation

Uses DSPy to intelligently generate nodes and schemas at SETUP TIME.
Pipecat Flows handles all conversation routing at RUNTIME.

Key Philosophy:
- DSPy = Smart generation (analyze prompt, extract structure, create schemas)
- Pipecat = Runtime execution (conversation flow, routing, state)

Architecture:
┌─────────────────────────────────────────────────────────────┐
│                   GENERATION TIME (DSPy)                     │
├─────────────────────────────────────────────────────────────┤
│  1. Intelligent Segment Classification                      │
│  2. Smart Field Extraction                                  │
│  3. Schema Generation with Context                          │
│  4. Task Message Creation                                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
                   NodeConfig List
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   RUNTIME (Pipecat Flows)                    │
├─────────────────────────────────────────────────────────────┤
│  • Flow routing and transitions                             │
│  • Handler execution                                        │
│  • State management                                         │
│  • Context strategies                                       │
└─────────────────────────────────────────────────────────────┘

Author: AI Senior Architect
Date: 2025-11-08
"""
import json

import re
import os
import dspy
from enum import Enum
from typing import List, Optional, Dict, Any, Callable
from dataclasses import dataclass, field
from pipecat_flows import (
    FlowArgs,
    FlowManager,
    FlowResult,
    FlowsFunctionSchema,
    NodeConfig,
)
from dotenv import load_dotenv

from pipecat_flows import ContextStrategy, ContextStrategyConfig

from super.core.voice.workflows.flows.conversation_flow import create_flow_from_plan
from super.core.voice.workflows.flows.pydantic_ai_section_parser import parse_conversation_plan_async
from super.core.voice.workflows.flows.section_parser import SectionParser
from super.core.voice.workflows.flows.react_node_builder import create_react_flow

# V2 Architecture imports
from super.core.voice.workflows.flows.react_node_builder_v2 import (
    FunctionRegistry,
    ReActNodeBuilderV2,
    ReActFlowConverterV2
)

load_dotenv(override=True)

# Import DSPy configuration manager
from ..dspy_config import get_dspy_lm


# ============================================================================
# SECTION 1: REUSE V2 BASE STRUCTURES
# ============================================================================

# ============================================================================
# SECTION 1: CORE DATA MODELS (REBASING FROM V2 ARCHITECTURE)
# ============================================================================


class SegmentType(Enum):
    INSTRUCTIONS = "instructions"
    IDENTITY = "identity"
    GOAL = "goal"
    QA = "qa"
    ACTION = "action"
    CONDITION = "condition"
    RESIDUAL = "residual"


@dataclass
class PromptSegment:
    segment_id: str
    segment_type: SegmentType
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GoalItem:
    goal_id: str
    title: str
    description: str
    required_fields: List[str]
    status: str
    content: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QAPair:
    question: str
    answer: str
    keywords: List[str] = field(default_factory=list)


@dataclass
class Action:
    action_id: str
    name: str
    description: str
    handler: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MacroNode:
    node_id: str
    node_type: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FlowBlueprint:
    instructions: MacroNode
    identity: MacroNode
    goals: List[GoalItem]
    qa_pairs: List[QAPair]
    actions: List[Action]
    conditions: Dict[str, Any]
    residuals: List[str]


@dataclass
class GoalRuntimeConfig:
    """Runtime metadata for each goal node after DSPy schema generation."""

    goal: GoalItem
    function_name: str
    required_fields: List[str]
    function_description: str
    task_message: str



class ContextStrategyResolver:
    """Assign context strategies to nodes consistently."""

    SUMMARY_PROMPTS = {
        "instructions": "Summarize the most critical guardrails the agent must always follow.",
        "identity": "Reiterate the persona, organization, and tone the agent must embody.",
        "goal": "Provide a concise summary of the fields collected so far so the next step can build on it.",
        "qa": "Summarize the key facts shared while answering this question.",
        "action": "Capture any action needs to be taken and why.",
        "end": "Summarize the entire conversation in one sentence before closing.",
    }

    STRATEGY_MAP = {
        "instructions": ContextStrategy.APPEND,
        "identity": ContextStrategy.APPEND,
        "goal": ContextStrategy.RESET_WITH_SUMMARY,
        "qa": ContextStrategy.RESET_WITH_SUMMARY,
        "action": ContextStrategy.RESET_WITH_SUMMARY,
        "end": ContextStrategy.RESET,
    }

    def resolve(self, node_type: str) -> ContextStrategyConfig:
        strategy = self.STRATEGY_MAP.get(node_type, ContextStrategy.RESET_WITH_SUMMARY)
        summary = self.SUMMARY_PROMPTS.get(node_type)
        return ContextStrategyConfig(strategy=strategy, summary_prompt=summary)


# ============================================================================
# SECTION 2: DSPy SIGNATURES FOR GENERATION
# ============================================================================

class SegmentClassificationSignature(dspy.Signature):
    """Intelligently classify a prompt segment."""
    segment_header = dspy.InputField(desc="Section header/title")
    segment_content = dspy.InputField(desc="Section content (first 300 chars)")

    segment_type = dspy.OutputField(
        desc="Type: 'identity', 'instructions', 'goal', 'qa', 'condition', 'action', or 'residual'"
    )
    confidence = dspy.OutputField(desc="Confidence score 0-100")
    reasoning = dspy.OutputField(desc="Why this classification")


class FieldExtractionSignature(dspy.Signature):
    """Extract data fields from a goal/question."""
    goal_content = dspy.InputField(desc="The goal or question text")

    extracted_fields = dspy.OutputField(desc="Comma-separated field names (e.g., 'name,phone,email')")
    field_descriptions = dspy.OutputField(desc="Brief description for each field")
    reasoning = dspy.OutputField(desc="Extraction logic")


class SchemaGenerationSignature(dspy.Signature):
    """Generate function schema for a goal node."""
    goal_description = dspy.InputField(desc="What this goal aims to collect")
    extracted_fields = dspy.InputField(desc="Fields to collect")

    function_name = dspy.OutputField(desc="Suggested function name (snake_case)")
    function_description = dspy.OutputField(desc="Clear description of what function does")
    required_fields = dspy.OutputField(desc="Which fields are required (comma-separated)")


class TaskMessageGenerationSignature(dspy.Signature):
    """Generate task message for a node."""
    node_type = dspy.InputField(desc="Node type (identity, goal, qa, etc)")
    original_content = dspy.InputField(desc="Original prompt content for this node")
    context = dspy.InputField(desc="Additional context (multi-language, fields, etc)")

    task_message = dspy.OutputField(desc="Clear task instruction for LLM")
    reasoning = dspy.OutputField(desc="Why this task message")


# ============================================================================
# SECTION 3: DSPy-ENHANCED SEGMENTER
# ============================================================================

class IntelligentPromptSegmenter:
    """
    Parse prompts using DSPy for intelligent classification.

    V2 used keywords, V3 uses LLM reasoning for better accuracy.
    """

    def __init__(self, lm=None):
        self.lm = lm or get_dspy_lm()
        self.classifier = dspy.ChainOfThought(SegmentClassificationSignature)

    def segment(self, system_prompt: str) -> List[PromptSegment]:
        """Parse prompt into typed segments using DSPy."""
        normalized = self._normalize(system_prompt)
        raw_sections = self._split_sections(normalized)

        segments = []
        for idx, section in enumerate(raw_sections):
            seg_type = self._classify_with_dspy(section["name"], section["content"])

            segment = PromptSegment(
                segment_id=f"seg_{idx}",
                segment_type=seg_type,
                content=section["content"],
                metadata={"header": section["name"]}
            )
            segments.append(segment)

        return segments

    def _normalize(self, text: str) -> str:
        """Normalize whitespace and line breaks."""
        # Handle both literal escaped newlines (\r\n as string) and actual CR+LF
        text = text.replace('\\r\\n', '\n')  # Convert literal \r\n to actual newline
        text = text.replace('\\n', '\n')    # Convert literal \n to actual newline
        text = re.sub(r'\r\n', '\n', text)  # Convert actual CR+LF to LF
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def _split_sections(self, text: str) -> List[Dict[str, str]]:
        """Split into sections by headers."""
        # Pattern: [Header] or # Header or == Header ==
        pattern = r'(?:^|\n)(?:\[([^\]]+)\]|#+\s*([^\n]+)|==+\s*([^\n]+)\s*==+)'

        matches = list(re.finditer(pattern, text, re.MULTILINE))

        if not matches:
            # No headers, treat entire text as one section
            return [{
                "name": "Main Content",
                "content": text.strip(),
                "start": 0,
                "end": len(text)
            }]

        sections = []
        for i, match in enumerate(matches):
            header = match.group(1) or match.group(2) or match.group(3)
            header = header.strip()

            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)

            content = text[start:end].strip()

            if content:  # Skip empty sections
                sections.append({
                    "name": header,
                    "content": content,
                    "start": start,
                    "end": end
                })

        parser = SectionParser()

        # Extract sections first (not parsing yet)
        sections_alt = parser._extract_sections_from_prompt(text)

        return sections

    def _classify_with_dspy(self, header: str, content: str) -> SegmentType:
        """Use DSPy to classify segment type."""
        with dspy.context(lm=self.lm):
            # Truncate content for API efficiency
            content_preview = content[:300] + ("..." if len(content) > 300 else "")

            result = self.classifier(
                segment_header=header,
                segment_content=content_preview
            )

            # Map to SegmentType enum
            type_map = {
                'identity': SegmentType.IDENTITY,
                'instructions': SegmentType.INSTRUCTIONS,
                'goal': SegmentType.GOAL,
                'qa': SegmentType.QA,
                'conditional': SegmentType.CONDITION,
                'condition': SegmentType.CONDITION,
                'action': SegmentType.ACTION,
                'residual': SegmentType.RESIDUAL
            }

            seg_type = type_map.get(result.segment_type.lower(), SegmentType.RESIDUAL)

            print(f"[DSPy Classify] {header[:30]:<30} → {seg_type.value:<15} (confidence: {result.confidence})")

            return seg_type


# ============================================================================
# SECTION 4: DSPy-ENHANCED BLUEPRINT BUILDER
# ============================================================================

class IntelligentBlueprintBuilder:
    """
    Build FlowBlueprint using DSPy for intelligent extraction.

    Enhancements over V2:
    - Smarter field extraction
    - Better schema generation
    - Context-aware task messages
    """

    def __init__(self, lm=None):
        self.lm = lm or get_dspy_lm()
        self.field_extractor = dspy.ChainOfThought(FieldExtractionSignature)
        self.schema_generator = dspy.ChainOfThought(SchemaGenerationSignature)

    def build(self, segments: List[PromptSegment]) -> FlowBlueprint:
        """Build blueprint from segments using DSPy intelligence."""

        # Group by type
        by_type = self._group_by_type(segments)

        # Build macro-nodes
        instructions = self._build_instructions_node(by_type.get(SegmentType.INSTRUCTIONS, []))
        identity = self._build_identity_node(by_type.get(SegmentType.IDENTITY, []))
        goals = self._build_goals_with_dspy(by_type.get(SegmentType.GOAL, []))
        qa_pairs = self._build_qa_registry(by_type.get(SegmentType.QA, []))
        actions = self._build_action_catalog(by_type.get(SegmentType.ACTION, []))
        conditions = self._build_conditions(by_type.get(SegmentType.CONDITION, []))
        residuals = [seg.content for seg in by_type.get(SegmentType.RESIDUAL, [])]

        return FlowBlueprint(
            instructions=instructions,
            identity=identity,
            goals=goals,
            qa_pairs=qa_pairs,
            actions=actions,
            conditions=conditions,
            residuals=residuals
        )

    def _group_by_type(self, segments: List[PromptSegment]) -> Dict[SegmentType, List[PromptSegment]]:
        """Group segments by type."""
        grouped = {}
        for seg in segments:
            if seg.segment_type not in grouped:
                grouped[seg.segment_type] = []
            grouped[seg.segment_type].append(seg)
        return grouped

    def _build_instructions_node(self, segments: List[PromptSegment]) -> MacroNode:
        """Build instructions macro-node."""
        if not segments:
            return MacroNode(
                node_id="instructions",
                node_type="instructions",
                content="Follow conversation best practices. Be helpful and professional.",
                metadata={"segments": 0}
            )

        # Combine all instruction segments
        combined = "\n\n".join([seg.content for seg in segments])
        return MacroNode(
            node_id="instructions",
            node_type="instructions",
            content=combined,
            metadata={"segments": len(segments)}
        )

    def _build_identity_node(self, segments: List[PromptSegment]) -> MacroNode:
        """Build identity macro-node."""
        if not segments:
            return MacroNode(
                node_id="identity",
                node_type="identity",
                content="You are a helpful AI assistant. Introduce yourself and assist the user.",
                metadata={"segments": 0}
            )

        combined = "\n\n".join([seg.content for seg in segments])
        return MacroNode(
            node_id="identity",
            node_type="identity",
            content=combined,
            metadata={"segments": len(segments)}
        )

    def _build_goals_with_dspy(self, segments: List[PromptSegment]) -> List[GoalItem]:
        """Build goals using DSPy for intelligent field extraction."""
        if not segments:
            # Default goal
            return [GoalItem(
                goal_id="goal_0",
                title="default_goal",
                description="Help the user with their request",
                required_fields=["user_request"],
                status="pending",
                content="Help the user with their request",
                metadata={"auto_generated": True}
            )]

        goals = []
        for i, seg in enumerate(segments):
            goal_id = f"goal_{i}"
            title = seg.metadata.get("header") or goal_id

            # Use DSPy to extract fields
            fields, description = self._extract_fields_with_dspy(seg.content)

            goal = GoalItem(
                goal_id=goal_id,
                title=title,
                description=f"{title}\n\n{seg.content}".strip(),
                required_fields=fields if fields else ["response"],
                status="pending",
                content=seg.content,
                metadata={"header": title, "field_hints": description}
            )
            goals.append(goal)

        return goals

    def _extract_fields_with_dspy(self, content: str) -> tuple[List[str], str]:
        """Extract fields from goal content using DSPy."""
        with dspy.context(lm=self.lm):
            result = self.field_extractor(goal_content=content[:500])

            # Parse comma-separated fields
            fields_str = result.extracted_fields.strip()
            fields = [f.strip() for f in fields_str.split(',') if f.strip()]

            # Clean up field names (remove invalid chars)
            cleaned_fields = []
            for field in fields:
                # Only alphanumeric and underscore
                clean = re.sub(r'[^a-zA-Z0-9_]', '', field.lower())
                if clean and len(clean) > 1:  # Avoid single-char fields
                    cleaned_fields.append(clean)

            print(f"[DSPy Extract] {content[:40]:<40} → fields: {cleaned_fields}")

            return cleaned_fields, result.field_descriptions

    def _build_qa_registry(self, segments: List[PromptSegment]) -> List[QAPair]:
        """Build Q&A pairs from FAQ/Q&A sections."""
        qa_pairs = []

        for seg in segments:
            # Parse Q: ... A: ... format
            pattern = r'Q:\s*(.+?)\s*A:\s*(.+?)(?=Q:|$)'
            matches = re.findall(pattern, seg.content, re.DOTALL | re.IGNORECASE)

            for question, answer in matches:
                question = question.strip()
                answer = answer.strip()

                # Extract keywords
                keywords = self._extract_keywords(question)

                qa_pairs.append(QAPair(
                    question=question,
                    answer=answer,
                    keywords=keywords
                ))

        return qa_pairs

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text."""
        # Remove common words and extract meaningful terms
        words = re.findall(r'\w+', text.lower())
        stopwords = {'is', 'the', 'what', 'how', 'can', 'do', 'you', 'i', 'a', 'an', 'to', 'in', 'for', 'of', 'on', 'with'}
        keywords = [w for w in words if w not in stopwords and len(w) > 3]
        return keywords[:5]  # Top 5

    def _build_action_catalog(self, segments: List[PromptSegment]) -> List[Action]:
        """Build action catalog."""
        actions = [
            Action(
                action_id="handover_call",
                name="handover_call",
                description="Transfer to human agent",
                handler="handover_call"
            ),
            Action(
                action_id="end_call",
                name="end_call",
                description="End conversation",
                handler="end_call"
            )
        ]

        # Parse custom actions from segments
        for seg in segments:
            # Look for action patterns like [Action Name] or "action: ..."
            pass  # TODO: Implement custom action parsing if needed

        return actions

    def _build_conditions(self, segments: List[PromptSegment]) -> Dict[str, Any]:
        """Build conditional branching map."""
        conditions = {}

        for seg in segments:
            content = seg.content.lower()

            if 'if yes' in content or 'if positive' in content:
                conditions['on_yes'] = seg.content
            elif 'if no' in content or 'if negative' in content:
                conditions['on_no'] = seg.content

        return conditions


# ============================================================================
# SECTION 4A: CONVERTER - PARSED CONFIG TO BLUEPRINT
# ============================================================================

def build_blueprint_from_parsed_config(config) -> FlowBlueprint:
    """
    Convert ParsedFlowConfig (from section_parser) to FlowBlueprint (for V3).

    This is the HYBRID APPROACH:
    - Use section_parser for deterministic structure extraction
    - Convert to FlowBlueprint format
    - Let DSPy enhance schemas and task messages in compilation

    Args:
        config: ParsedFlowConfig from SectionParser

    Returns:
        FlowBlueprint ready for IntelligentNodeCompiler
    """

    # Build instructions MacroNode
    instructions_content = ""
    if config.instructions:
        instructions_content = config.instructions.content

    # Merge guidelines into instructions
    if config.guidelines:
        guideline_texts = [g.content for g in config.guidelines]
        guidelines_combined = "\n\n".join(guideline_texts)
        if instructions_content:
            instructions_content = f"{instructions_content}\n\n{guidelines_combined}"
        else:
            instructions_content = guidelines_combined

    if not instructions_content:
        instructions_content = "Follow conversation best practices. Be helpful and professional."

    instructions = MacroNode(
        node_id="instructions",
        node_type="instructions",
        content=instructions_content,
        metadata={"from_parser": True}
    )

    # Build identity MacroNode
    identity_content = ""
    if config.identity:
        identity_content = config.identity.content

    if not identity_content:
        identity_content = "You are a helpful AI assistant. Introduce yourself and assist the user."

    identity = MacroNode(
        node_id="identity",
        node_type="identity",
        content=identity_content,
        metadata={"from_parser": True}
    )

    # Convert questions and pitches to goals (tasks)
    # IMPORTANT: Only convert sections that are actual data collection steps
    # Conditions and objections should NOT become sequential goals
    goals: List[GoalItem] = []

    # Process questions as goals/tasks
    for idx, question in enumerate(config.questions):
        # Ensure we have at least one required field
        required = question.required if question.required else ["response"]

        goal = GoalItem(
            goal_id=question.id,
            title=question.section_name,
            description=question.content,
            required_fields=required,
            status="pending",
            content=question.content,
            metadata={
                "section_type": "question",
                "field_types": question.field_types or {},
                "field_descriptions": question.field_descriptions or {}
            }
        )
        goals.append(goal)

    # Process pitches as goals too (they're conversation steps)
    for idx, pitch in enumerate(config.pitches):
        # Ensure we have at least one required field
        required = pitch.required if pitch.required else ["response"]

        goal = GoalItem(
            goal_id=pitch.id,
            title=pitch.section_name,
            description=pitch.content,
            required_fields=required,
            status="pending",
            content=pitch.content,
            metadata={
                "section_type": "pitch",
                "field_types": pitch.field_types or {},
                "field_descriptions": pitch.field_descriptions or {}
            }
        )
        goals.append(goal)

    # If no goals found, create default
    if not goals:
        goals = [GoalItem(
            goal_id="goal_0",
            title="default_goal",
            description="Help the user with their request",
            required_fields=["user_request"],
            status="pending",
            content="Help the user with their request",
            metadata={"auto_generated": True}
        )]

    # Convert FAQs to QA pairs
    qa_pairs: List[QAPair] = []
    for faq in config.faqs:
        # Parse Q: ... A: ... format
        pattern = r'Q:\s*(.+?)\s*A:\s*(.+?)(?=Q:|$)'
        matches = re.findall(pattern, faq.content, re.DOTALL | re.IGNORECASE)

        for question, answer in matches:
            question = question.strip()
            answer = answer.strip()

            # Extract keywords from question
            words = re.findall(r'\w+', question.lower())
            stopwords = {'is', 'the', 'what', 'how', 'can', 'do', 'you', 'i', 'a', 'an', 'to', 'in', 'for', 'of', 'on', 'with'}
            keywords = [w for w in words if w not in stopwords and len(w) > 3][:5]

            qa_pairs.append(QAPair(
                question=question,
                answer=answer,
                keywords=keywords
            ))

    # Build actions catalog
    actions = [
        Action(
            action_id="handover_call",
            name="handover_call",
            description="Transfer to human agent",
            handler="handover_call"
        ),
        Action(
            action_id="end_call",
            name="end_call",
            description="End conversation",
            handler="end_call"
        )
    ]

    # Process objections as actions or special handlers
    for objection in config.objections:
        # Sanitize action name to meet OpenAI's 64-char limit for function names
        action_name = re.sub(r'[^a-zA-Z0-9_-]', '_', objection.id)
        if len(action_name) > 64:
            action_name = action_name[:64].rstrip('_')

        action = Action(
            action_id=objection.id,
            name=action_name,  # Sanitized for OpenAI
            description=f"Handle objection: {objection.section_name}",
            handler=None,
            metadata={
                "trigger_keywords": objection.trigger_keywords,
                "content": objection.content
            }
        )
        actions.append(action)

    # Build conditions
    conditions = {}
    for condition in config.conditions:
        if condition.condition_type == 'yes':
            conditions['on_yes'] = condition.content
        elif condition.condition_type == 'no':
            conditions['on_no'] = condition.content
        else:
            conditions[condition.id] = condition.content

    # Collect residuals (anything else)
    residuals = []

    print(f"[Parser→Blueprint] Converted:")
    print(f"  ✓ Questions → Goals: {len(config.questions)}")
    print(f"  ✓ Pitches → Goals: {len(config.pitches)}")
    print(f"  ✓ Total Goals/Tasks: {len(goals)}")
    print(f"  ✓ FAQs → QA Pairs: {len(qa_pairs)}")
    print(f"  ✓ Actions: {len(actions)}")

    return FlowBlueprint(
        instructions=instructions,
        identity=identity,
        goals=goals,
        qa_pairs=qa_pairs,
        actions=actions,
        conditions=conditions,
        residuals=residuals
    )


# ============================================================================
# SECTION 4: FLOW ORCHESTRATOR (CANONICAL MACRO-NODES)
# ============================================================================


class FlowOrchestrator:
    """Compile FlowBlueprint + DSPy metadata into Pipecat nodes."""

    STATE_KEY = "flow_orchestrator_state"
    QA_NODE_NAME = "qa_router"
    ACTION_NODE_NAME = "action_router"
    END_NODE_NAME = "end"

    def __init__(
        self,
        blueprint: FlowBlueprint,
        goal_configs: List[GoalRuntimeConfig],
        context_strategy_resolver: Optional[ContextStrategyResolver] = None,
        get_docs_handler: Optional[Callable] = None,
        handover_handler: Optional[Callable] = None,
        end_call_handler: Optional[Callable] = None,
    ):
        self.blueprint = blueprint
        self.goal_configs = goal_configs
        self.context_resolver = context_strategy_resolver or ContextStrategyResolver()
        self.get_docs_handler = get_docs_handler
        self.handover_handler = handover_handler
        self.end_call_handler = end_call_handler
        self.node_lookup: Dict[str, NodeConfig] = {}
        self.goal_index_map = {
            cfg.goal.goal_id: idx for idx, cfg in enumerate(self.goal_configs)
        }

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def build_nodes(self) -> List[NodeConfig]:
        nodes: List[NodeConfig] = []

        next_after_identity = (
            self.goal_configs[0].goal.goal_id if self.goal_configs else self.QA_NODE_NAME
        )

        nodes.append(self._build_instructions_node(next_node="identity"))
        nodes.append(self._build_identity_node(next_node=next_after_identity))

        for idx, goal_cfg in enumerate(self.goal_configs):
            next_node = (
                self.goal_configs[idx + 1].goal.goal_id
                if idx + 1 < len(self.goal_configs)
                else self.QA_NODE_NAME
            )
            nodes.append(self._build_goal_node(goal_cfg, next_node=next_node))

        nodes.append(self._build_qa_node(next_node=self.ACTION_NODE_NAME))
        nodes.append(self._build_action_node(next_node=self.END_NODE_NAME))
        nodes.append(self._build_end_node())

        # Register nodes for runtime lookups
        self.node_lookup = {node["name"]: node for node in nodes}

        # Inject global handlers (questions/actions)
        self._inject_global_functions(nodes)

        return nodes

    # ------------------------------------------------------------------ #
    # Node Builders
    # ------------------------------------------------------------------ #

    def _build_instructions_node(self, next_node: str) -> NodeConfig:
        handler = self._make_simple_transition_handler("instructions", next_node)
        function = FlowsFunctionSchema(
            name="acknowledge_instructions",
            handler=handler,
            description="Acknowledge the guidelines and move to the identity step.",
            properties={},
            required=[],
        )
        role_messages = [{"role": "system", "content": self.blueprint.instructions.content}]
        task_messages = [
            {
                "role": "system",
                "content": "Absorb these guardrails and confirm you understand them before speaking with the user.",
            }
        ]
        return self._build_node(
            name="instructions",
            node_type="instructions",
            role_messages=role_messages,
            task_messages=task_messages,
            functions=[function],
            respond_immediately=False,
        )

    def _build_identity_node(self, next_node: str) -> NodeConfig:
        handler = self._make_simple_transition_handler("identity", next_node)
        function = FlowsFunctionSchema(
            name="confirm_identity",
            handler=handler,
            description="Confirm the agent identity and begin the scripted flow.",
            properties={},
            required=[],
        )
        supplemental = "\n\n".join(self.blueprint.residuals) if self.blueprint.residuals else ""
        content = f"{self.blueprint.identity.content}\n\n{supplemental}".strip()
        role_messages = [{"role": "system", "content": content}]
        task_messages = [
            {
                "role": "system",
                "content": "Introduce yourself naturally using this persona before collecting any information.",
            }
        ]
        return self._build_node(
            name="identity",
            node_type="identity",
            role_messages=role_messages,
            task_messages=task_messages,
            functions=[function],
            respond_immediately=True,
        )

    def _build_goal_node(self, goal_cfg: GoalRuntimeConfig, next_node: str) -> NodeConfig:
        # Build properties dict for function schema
        properties = {
            field: {
                "type": "string",
                "description": f"Value captured for {field.replace('_', ' ')}",
            }
            for field in goal_cfg.required_fields
        }

        # Defensive validation: ensure properties is always a dict (never list/None)
        if not isinstance(properties, dict):
            print(f"⚠️  WARNING: properties for {goal_cfg.goal.goal_id} was {type(properties)}, converting to empty dict")
            properties = {}

        # Ensure required_fields is a list
        required_fields = goal_cfg.required_fields if isinstance(goal_cfg.required_fields, list) else []

        handler = self._make_goal_handler(goal_cfg, next_node)
        function = FlowsFunctionSchema(
            name=goal_cfg.function_name,
            handler=handler,
            description=goal_cfg.function_description,
            properties=properties,
            required=required_fields,
        )
        role_messages = [
            {
                "role": "system",
                "content": f"**CURRENT STEP:** {goal_cfg.goal.title}\n\nCollect: {', '.join(goal_cfg.required_fields)}",
            }
        ]
        task_messages = [
            {
                "role": "system",
                "content": goal_cfg.task_message or goal_cfg.goal.description,
            }
        ]
        return self._build_node(
            name=goal_cfg.goal.goal_id,
            node_type="goal",
            role_messages=role_messages,
            task_messages=task_messages,
            functions=[function],
            respond_immediately=True,
        )

    def _build_qa_node(self, next_node: str) -> NodeConfig:
        handler = self._make_simple_transition_handler(self.QA_NODE_NAME, next_node)
        function = FlowsFunctionSchema(
            name="confirm_questions_addressed",
            handler=handler,
            description="Confirm that the user's questions (if any) have been answered before moving on.",
            properties={},
            required=[],
        )
        if self.blueprint.qa_pairs:
            qa_context = "\n\n".join(
                [f"Q: {pair.question}\nA: {pair.answer}" for pair in self.blueprint.qa_pairs]
            )
        else:
            qa_context = "Use the knowledge base or available tools to answer any outstanding questions."
        role_messages = [
            {
                "role": "system",
                "content": "Review outstanding user questions. Use the provided answers below or call get_docs if needed.",
            }
        ]
        task_messages = [
            {
                "role": "system",
                "content": qa_context,
            }
        ]
        return self._build_node(
            name=self.QA_NODE_NAME,
            node_type="qa",
            role_messages=role_messages,
            task_messages=task_messages,
            functions=[function],
            respond_immediately=True,
        )

    def _build_action_node(self, next_node: str) -> NodeConfig:
        handler = self._make_simple_transition_handler(self.ACTION_NODE_NAME, next_node)
        function = FlowsFunctionSchema(
            name="complete_actions",
            handler=handler,
            description="Confirm whether any pending actions need to be triggered before ending the conversation.",
            properties={},
            required=[],
        )
        available_actions = ", ".join([action.name for action in self.blueprint.actions])
        role_messages = [
            {
                "role": "system",
                "content": f"Available actions: {available_actions}. Trigger actions if the user explicitly asks.",
            }
        ]
        task_messages = [
            {
                "role": "system",
                "content": "Check if the user needs a handover, callback, or wants to end the call. Call the appropriate function.",
            }
        ]
        return self._build_node(
            name=self.ACTION_NODE_NAME,
            node_type="action",
            role_messages=role_messages,
            task_messages=task_messages,
            functions=[function],
            respond_immediately=True,
        )

    def _build_end_node(self) -> NodeConfig:
        handler = self._make_simple_transition_handler(self.END_NODE_NAME, None)
        function = FlowsFunctionSchema(
            name="complete_conversation",
            handler=handler,
            description="Thank the user and end the conversation gracefully.",
            properties={},
            required=[],
        )
        role_messages = [
            {
                "role": "system",
                "content": "Thank the caller for their time, summarize next steps, and politely end the call.",
            }
        ]
        task_messages = [
            {
                "role": "system",
                "content": "Deliver a short, warm closing message.",
            }
        ]
        return self._build_node(
            name=self.END_NODE_NAME,
            node_type="end",
            role_messages=role_messages,
            task_messages=task_messages,
            functions=[function],
            respond_immediately=True,
        )

    # ------------------------------------------------------------------ #
    # Helper Builders
    # ------------------------------------------------------------------ #

    def _build_node(
        self,
        name: str,
        node_type: str,
        role_messages: List[Dict[str, Any]],
        task_messages: List[Dict[str, Any]],
        functions: List[FlowsFunctionSchema],
        respond_immediately: bool,
    ) -> NodeConfig:
        node = NodeConfig(
            name=name,
            role_messages=role_messages,
            task_messages=task_messages,
            functions=functions,
            respond_immediately=respond_immediately,
        )
        node["context_strategy"] = self.context_resolver.resolve(node_type)
        return node

    def _build_result_class(self, label: str, fields: Optional[List[str]] = None):
        attrs: Dict[str, Any] = {}
        if fields:
            for field in fields:
                attrs[field] = str
        else:
            attrs["status"] = str
        return type(f"{label.title().replace('_', '')}Result", (FlowResult,), attrs)

    def _make_simple_transition_handler(self, step_name: str, next_node_name: Optional[str]):
        result_cls = self._build_result_class(step_name, fields=None)

        async def handler(args: FlowArgs, flow_manager: FlowManager):
            state = self._ensure_state(flow_manager)
            state["last_node"] = step_name
            state["resume_node"] = next_node_name or self.END_NODE_NAME
            next_node = self._resolve_node(next_node_name) if next_node_name else None
            return result_cls(status="completed"), next_node

        return handler

    def _make_goal_handler(self, goal_cfg: GoalRuntimeConfig, next_node: str):
        result_cls = self._build_result_class(goal_cfg.goal.goal_id, goal_cfg.required_fields)

        async def handler(args: FlowArgs, flow_manager: FlowManager):
            state = self._ensure_state(flow_manager)
            missing = [field for field in goal_cfg.required_fields if not args.get(field)]
            if missing:
                state["resume_node"] = goal_cfg.goal.goal_id
                return None, self._resolve_node(goal_cfg.goal.goal_id)

            collected = {field: args.get(field) for field in goal_cfg.required_fields}
            state["collected_data"][goal_cfg.goal.goal_id] = collected
            if goal_cfg.goal.goal_id not in state["completed_goals"]:
                state["completed_goals"].append(goal_cfg.goal.goal_id)
            state["current_goal_index"] = self.goal_index_map.get(goal_cfg.goal.goal_id, 0) + 1
            state["resume_node"] = next_node
            next_node_cfg = self._resolve_node(next_node)
            return result_cls(**collected), next_node_cfg

        return handler

    # ------------------------------------------------------------------ #
    # Global Handlers (Questions + Actions)
    # ------------------------------------------------------------------ #

    def _inject_global_functions(self, nodes: List[NodeConfig]):
        for node in nodes:
            name = node.get("name")
            if name == self.END_NODE_NAME:
                continue
            functions = node.get("functions", [])
            functions.append(self._build_question_function(origin_node=name))
            for action in self.blueprint.actions:
                action_function = self._build_action_function(action)
                if action_function:
                    functions.append(action_function)
            node["functions"] = functions

    def _build_question_function(self, origin_node: str) -> FlowsFunctionSchema:
        result_cls = self._build_result_class("answer_question", fields=["answer"])

        async def handler(args: FlowArgs, flow_manager: FlowManager):
            question = args.get("question", "")
            state = self._ensure_state(flow_manager)
            state["resume_node"] = origin_node
            answer = self._find_qa_answer(question)
            if answer:
                state["last_answer"] = answer
                return result_cls(answer=answer), self._resolve_node(origin_node)
            if self.get_docs_handler:
                try:
                    args["query"] = question
                except Exception:
                    pass
                await self.get_docs_handler(args, flow_manager)
            return None, self._resolve_node(origin_node)

        return FlowsFunctionSchema(
            name=f"answer_question_{origin_node}",
            handler=handler,
            description="Answer the user's question without leaving the current step.",
            properties={
                "question": {"type": "string", "description": "The user's exact question"}
            },
            required=["question"],
        )

    def _build_action_function(self, action: Action) -> Optional[FlowsFunctionSchema]:
        handler_callable = self._resolve_action_callable(action)

        if handler_callable is None:
            return None

        async def handler(args: FlowArgs, flow_manager: FlowManager):
            await handler_callable(args, flow_manager)
            state = self._ensure_state(flow_manager)
            state["last_action"] = action.name
            return None, self._resolve_node(self.END_NODE_NAME)

        # Defensive: ensure properties is a valid dict for OpenAI function schema
        # Metadata might contain non-schema fields like trigger_keywords (list), content (str)
        # We need to filter to only include valid property schemas
        properties = {}
        if isinstance(action.metadata, dict):
            # Only include fields that look like schema properties (type: dict with 'type' or 'description')
            for key, value in action.metadata.items():
                if isinstance(value, dict) and ('type' in value or 'description' in value):
                    properties[key] = value

        return FlowsFunctionSchema(
            name=action.name,
            handler=handler,
            description=action.description,
            properties=properties,  # Always a dict, never a list
            required=[],
        )

    # ------------------------------------------------------------------ #
    # State / Utility helpers
    # ------------------------------------------------------------------ #

    def _ensure_state(self, flow_manager: FlowManager) -> Dict[str, Any]:
        if not hasattr(flow_manager, "state") or flow_manager.state is None:
            flow_manager.state = {}
        if self.STATE_KEY not in flow_manager.state:
            flow_manager.state[self.STATE_KEY] = {
                "current_goal_index": 0,
                "completed_goals": [],
                "collected_data": {},
                "resume_node": "instructions",
                "last_node": None,
                "last_action": None,
            }
        return flow_manager.state[self.STATE_KEY]

    def _resolve_node(self, node_name: Optional[str]) -> Optional[NodeConfig]:
        if node_name is None:
            return None
        return self.node_lookup.get(node_name)

    def _find_qa_answer(self, question: str) -> Optional[str]:
        if not question:
            return None
        q_lower = question.lower()
        for pair in self.blueprint.qa_pairs:
            if any(keyword and keyword in q_lower for keyword in pair.keywords):
                return pair.answer
            if pair.question.lower() in q_lower:
                return pair.answer
        return None

    def _resolve_action_callable(self, action: Action) -> Optional[Callable]:
        if action.name == "handover_call" and self.handover_handler:
            return self.handover_handler
        if action.name == "end_call" and self.end_call_handler:
            return self.end_call_handler
        # Custom actions may not have handlers yet; stub them to no-op
        async def noop(*_args, **_kwargs):
            return None

        return noop


# ============================================================================
# SECTION 5: DSPy-ENHANCED NODE COMPILER
# ============================================================================

class IntelligentNodeCompiler:
    """
    Compile blueprint to NodeConfig using DSPy for schema generation.

    Output is standard Pipecat NodeConfig - no runtime DSPy calls.
    """

    def __init__(self, blueprint: FlowBlueprint, lm=None):
        self.blueprint = blueprint
        self.lm = lm or get_dspy_lm()
        self.schema_generator = dspy.ChainOfThought(SchemaGenerationSignature)
        self.task_message_generator = dspy.ChainOfThought(TaskMessageGenerationSignature)

    def compile(
        self,
        get_docs_handler: Optional[Callable] = None,
        handover_handler: Optional[Callable] = None,
        end_call_handler: Optional[Callable] = None
    ) -> List[NodeConfig]:
        """Compile blueprint to NodeConfig objects."""
        goal_configs = [self._prepare_goal_runtime(goal) for goal in self.blueprint.goals]

        orchestrator = FlowOrchestrator(
            blueprint=self.blueprint,
            goal_configs=goal_configs,
            context_strategy_resolver=ContextStrategyResolver(),
            get_docs_handler=get_docs_handler,
            handover_handler=handover_handler,
            end_call_handler=end_call_handler,
        )

        return orchestrator.build_nodes()

    def _prepare_goal_runtime(self, goal: GoalItem) -> GoalRuntimeConfig:
        """Generate runtime metadata for a goal using DSPy."""
        with dspy.context(lm=self.lm):
            schema_result = self.schema_generator(
                goal_description=goal.description[:200],
                extracted_fields=", ".join(goal.required_fields),
            )

            required_str = (schema_result.required_fields or "").strip()
            required = [field.strip() for field in required_str.split(",") if field.strip()]
            if not required:
                required = goal.required_fields

            task_message = self._generate_task_message(goal)

            # Ensure function name is valid and within OpenAI's 64-char limit
            function_name = self._sanitize_function_name(
                schema_result.function_name or goal.goal_id
            )

            print(
                f"[DSPy Schema] {goal.goal_id:<12} → "
                f"function: {function_name}, required: {required}"
            )

            return GoalRuntimeConfig(
                goal=goal,
                function_name=function_name,
                required_fields=required,
                function_description=schema_result.function_description or goal.description,
                task_message=task_message,
            )

    def _sanitize_function_name(self, name: str) -> str:
        """
        Sanitize function name to meet OpenAI requirements:
        - Max 64 characters
        - Only a-z, A-Z, 0-9, underscores, hyphens
        - Must match ^[a-zA-Z0-9_-]{1,64}$
        """
        # Remove invalid characters
        sanitized = re.sub(r'[^a-zA-Z0-9_-]', '_', name)

        # Truncate to 64 chars
        if len(sanitized) > 64:
            sanitized = sanitized[:64]

        # Ensure it doesn't end with underscore (aesthetic)
        sanitized = sanitized.rstrip('_')

        return sanitized

    def _generate_task_message(self, goal: GoalItem) -> str:
        """Generate contextual task message using DSPy (fallback to original content)."""
        try:
            with dspy.context(lm=self.lm):
                result = self.task_message_generator(
                    node_type="goal",
                    original_content=goal.content or goal.description,
                    context=f"Collect fields: {', '.join(goal.required_fields)}",
                )
                task_message = (result.task_message or "").strip()
                if task_message:
                    return task_message
        except Exception:
            pass

        return goal.description


# ============================================================================
# SECTION 6: ENTRY POINT
# ============================================================================

async def create_smart_flow(
    system_prompt: str,
    assistant_prompt: Optional[str] = None,
    get_docs_handler: Optional[Callable] = None,
    handover_handler: Optional[Callable] = None,
    end_call_handler: Optional[Callable] = None,
    lm=None
) -> List[NodeConfig]:
    """
    Generate flow with HYBRID intelligence at GENERATION time.

    HYBRID APPROACH:
    1. Parse with SectionParser (deterministic, proven, fast, free)
    2. Convert to FlowBlueprint
    3. Enhance with DSPy (better schemas and task messages)
    4. Output standard NodeConfig (Pipecat handles runtime)

    This gives us:
    - Reliable structure extraction (section_parser)
    - Intelligent enhancements (DSPy)
    - Best of both worlds

    Args:
        system_prompt: Full prompt text
        assistant_prompt: Optional identity context
        get_docs_handler: KB search function
        handover_handler: Human transfer function
        end_call_handler: Call termination function

    Returns:
        List[NodeConfig] - Standard Pipecat nodes (no runtime DSPy)
    """
    print(f"\n{'='*60}")
    print(f"SMART FLOW GENERATOR V3 (HYBRID: Parser + DSPy)")
    print(f"{'='*60}")

    # Step 1: Parse with SectionParser (deterministic structure extraction)
    print("Step 1: Parsing prompt structure (SectionParser)...")
    parser = SectionParser()
    parsed_config = parser.parse_prompt(system_prompt)
    print(f"  Found {len(parsed_config.sections_by_id)} sections")
    print(f"  Questions: {len(parsed_config.questions)}")
    print(f"  Pitches: {len(parsed_config.pitches)}")
    print(f"  FAQs: {len(parsed_config.faqs)}")

    # Step 2: Convert to FlowBlueprint
    print("\nStep 2: Converting to FlowBlueprint...")
    blueprint = build_blueprint_from_parsed_config(parsed_config)

    # Inject assistant_prompt if provided
    if assistant_prompt:
        blueprint.identity.content = f"{assistant_prompt}\n\n{blueprint.identity.content}"
        print(f"  ✓ Injected assistant prompt")

    # Step 3: Compile with DSPy-enhanced schemas
    print("\nStep 3: Compiling nodes with DSPy schema generation...")
    compiler = IntelligentNodeCompiler(blueprint, lm=lm)
    nodes = compiler.compile(
        get_docs_handler=get_docs_handler,
        handover_handler=handover_handler,
        end_call_handler=end_call_handler
    )
    print(f"  Created {len(nodes)} nodes")

    print(f"\n✅ Smart flow generated!")
    print(f"{'='*60}\n")

    return nodes


# Backward compatibility
async def create_section_based_flow(
    system_prompt: str,
    assistant_prompt: Optional[str] = None,
    get_docs_handler: Optional[Callable] = None,
    handover_handler: Optional[Callable] = None,
    end_call_handler: Optional[Callable] = None,
    lm=None
) -> List[NodeConfig]:
    """Backward-compatible wrapper."""
    return await create_smart_flow(
        system_prompt,
        assistant_prompt,
        get_docs_handler,
        handover_handler,
        end_call_handler,
        lm=lm
    )


# ============================================================================
# REACT FLOW GENERATION V2 (Think → Act Loop with Communication)
# ============================================================================

def create_react_flow_v2(
    standard_nodes: List[Dict[str, Any]],
    instructions: str,
    identity: str,
    objections: Dict[str, str],
    get_docs_handler: Optional[Callable] = None,
    handover_handler: Optional[Callable] = None,
    end_call_handler: Optional[Callable] = None
) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Create ReAct flow using V2 architecture: Think → Act loop.

    Think nodes:
    - Have FULL context (instructions + identity + objections + state)
    - Have ALL functions registered
    - Can communicate to user (output to TTS)
    - Decide what action to take next

    Act nodes:
    - Execute specific function (silent)
    - Loop back to Think

    Args:
        standard_nodes: Standard nodes from create_smart_flow
        instructions: Full instructions text
        identity: Agent identity/persona
        objections: Map of objection_id -> content
        get_docs_handler: Handler for document search
        handover_handler: Handler for agent handover
        end_call_handler: Handler for call termination

    Returns:
        Tuple of (react_nodes, react_config)
    """
    # Build function registry
    function_registry = FunctionRegistry()

    # Register standard action functions using FlowsFunctionSchema
    if get_docs_handler:
        function_registry.search_docs = FlowsFunctionSchema(
            name="search_docs",
            handler=get_docs_handler,
            description="Search documentation for information",
            properties={
                "query": {
                    "type": "string",
                    "description": "The search query"
                }
            },
            required=["query"]
        )

    if handover_handler:
        function_registry.handover = FlowsFunctionSchema(
            name="handover",
            handler=handover_handler,
            description="Transfer to human agent",
            properties={
                "reason": {
                    "type": "string",
                    "description": "Reason for handover"
                }
            },
            required=["reason"]
        )

    if end_call_handler:
        function_registry.end_call = FlowsFunctionSchema(
            name="end_call",
            handler=end_call_handler,
            description="End the conversation",
            properties={
                "reason": {
                    "type": "string",
                    "description": "Reason for ending call"
                }
            },
            required=["reason"]
        )

    # Extract and register ALL functions from standard nodes
    registered_count = 0
    for node in standard_nodes:
        functions = node.get("functions", [])
        for func in functions:
            # Get function name (handle both dict and FlowsFunctionSchema)
            if isinstance(func, dict):
                func_name = func.get("name", "")
            else:
                func_name = getattr(func, "name", "")

            # Skip action functions (already registered above)
            if func_name in ["search_docs", "handover", "end_call"]:
                continue

            # Register all other functions (keep as FlowsFunctionSchema object)
            if func_name:
                function_registry.add_goal_function(func)
                registered_count += 1

    # Create builder
    builder = ReActNodeBuilderV2(
        instructions=instructions,
        identity=identity,
        objections=objections,
        function_registry=function_registry
    )

    # Create converter and generate ReAct nodes
    converter = ReActFlowConverterV2(builder)
    react_nodes = converter.convert_standard_nodes_to_react(standard_nodes)

    # Build config
    react_config = {
        "flow_type": "react_v2_simplified",
        "architecture": "Single Think node (communication + execution)",
        "num_think_nodes": len([n for n in react_nodes if n.get("metadata", {}).get("node_type") == "think"]),
        "num_act_nodes": 0,  # Simplified V2 has no separate Act nodes
        "total_functions": len(function_registry.get_all_functions()),
        "features": [
            "Single Think node handles entire conversation",
            "Think node can communicate to users via TTS",
            "Think node has ALL functions registered",
            "Functions execute within Think node",
            "Waits for user input after each turn",
            "No orphaned nodes or infinite loops",
            "Provides user feedback for time-consuming actions (search, API calls)",
            "Natural responses for quick interactions without announcements"
        ]
    }

    return react_nodes, react_config


# ============================================================================
# REACT FLOW GENERATION (Original - Think → Act → Observe Loop)
# ============================================================================

def save_to_json(plan_dict, param):
    with open(param, 'w') as f:
        json.dump(plan_dict, f, indent=4)


async def create_react_smart_flow(
    system_prompt: str,
    assistant_prompt: Optional[str] = None,
    get_docs_handler: Optional[Callable] = None,
    handover_handler: Optional[Callable] = None,
    end_call_handler: Optional[Callable] = None,
    enable_react: bool = True,
    use_v2_architecture: bool = False,
    use_v3_architecture: bool = True
) -> tuple[List[NodeConfig], Dict[str, Any]]:
    """
    Create ReAct-optimized conversation flow.

    ARCHITECTURE V2 SIMPLIFIED (Default):
    1. Parse prompt with SectionParser (structure extraction)
    2. Generate standard nodes with DSPy enhancement
    3. Create single Think node with ALL functions
    4. Think node handles: communication + function execution + user interaction

    Flow per turn:
    - User speaks → Think node receives input
    - Think outputs: "Let me search for that..." (TTS)
    - Think calls: search_docs() function
    - Think receives: search results
    - Think outputs: "Here's what I found..." (TTS)
    - Think waits for next user input

    ARCHITECTURE V1 (Legacy):
    1. Parse prompt with SectionParser (structure extraction)
    2. Generate standard nodes with DSPy enhancement
    3. Convert to ReAct loop: Think → Act → Observe → repeat

    BENEFITS:
    - Handles large prompts efficiently
    - Single node architecture (no orphaned nodes)
    - No infinite loops (waits for user input)
    - Think node can communicate AND execute functions
    - Better reasoning (explicit Think phase with communication)
    - Functions actually execute (not filtered out)
    - User gets feedback before actions execute

    Args:
        system_prompt: The agent prompt to parse
        assistant_prompt: Optional assistant persona
        get_docs_handler: Handler for document search
        handover_handler: Handler for agent handover
        end_call_handler: Handler for call termination
        enable_react: If False, returns standard flow (for comparison)
        use_v2_architecture: If True, uses V2 Think→Act (default), else uses V1
        use_v3_architecture : if True Use V3 Central Node -> Think Function -> Act

    Returns:
        Tuple of (nodes, react_config) where:
        - nodes: List of ReAct-optimized NodeConfig
        - react_config: Configuration and metadata about ReAct transformation
    """
    # Parse prompt structure
    parser = SectionParser()
    parsed_config = parser.parse_prompt(system_prompt)

    plan = await parse_conversation_plan_async(system_prompt)

    plan_dict = plan.model_dump()

    # save_to_json(plan_dict, 'conversation_plan.json')

    flow = await create_flow_from_plan(plan)

    # Generate standard nodes
    standard_nodes = await create_smart_flow(
        system_prompt,
        assistant_prompt,
        get_docs_handler,
        handover_handler,
        end_call_handler
    )

    # Return standard flow if ReAct disabled
    if not enable_react:
        return standard_nodes, {"flow_type": "standard"}

    # Extract ReAct components from parsed config
    instructions = parsed_config.instructions.content if parsed_config.instructions else ""
    if parsed_config.guidelines:
        guidelines_text = "\n\n".join(g.content for g in parsed_config.guidelines)
        instructions = f"{instructions}\n\n{guidelines_text}" if instructions else guidelines_text

    identity = parsed_config.identity.content if parsed_config.identity else ""
    if assistant_prompt:
        identity = f"{assistant_prompt}\n\n{identity}" if identity else assistant_prompt

    objections = {obj.id: obj.content for obj in parsed_config.objections}

    # Convert to ReAct flow (V2 or V1)
    if use_v2_architecture:
        # Use V2: Think (communicate + decide) → Act (execute)
        react_nodes, react_config = create_react_flow_v2(
            standard_nodes=standard_nodes,
            instructions=instructions,
            identity=identity,
            objections=objections,
            get_docs_handler=get_docs_handler,
            handover_handler=handover_handler,
            end_call_handler=end_call_handler
        )
    elif use_v3_architecture:
        from super.core.voice.workflows.flows.react_node_builder_v3 import create_react_flow_v3
        react_nodes, react_config = create_react_flow_v3(
            standard_nodes=standard_nodes,
            instructions=instructions,
            identity=identity,
            objections=objections,
            get_docs_handler=get_docs_handler,
            handover_handler=handover_handler,
            end_call_handler=end_call_handler
        )
    else:
        # Use V1: Think → Act → Observe (legacy)
        react_nodes, react_config = create_react_flow(
            standard_nodes=standard_nodes,
            instructions=instructions,
            identity=identity,
            objections=objections
        )

    # Enrich config with metadata
    react_config.update({
        "parsed_config": {
            "num_sections": len(parsed_config.sections_by_id),
            "num_questions": len(parsed_config.questions),
            "num_objections": len(parsed_config.objections),
            "num_faqs": len(parsed_config.faqs)
        },
        "instructions": instructions,
        "identity": identity,
        "objections": objections
    })

    return react_nodes, react_config
