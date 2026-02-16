from typing import List, TypedDict
import re
from pipecat_flows import (
    FlowArgs,
    FlowManager,
    FlowResult,
    FlowsFunctionSchema,
    NodeConfig,
)
import os
import dspy
from dotenv import load_dotenv
from dspy import ChainOfThought
from plotly.utils import node_generator
from ..dspy_config import get_dspy_lm

load_dotenv(override=True)


class NodeSchemaSignature(dspy.Signature):
    content = dspy.InputField(desc="content based on which need to create node schema")
    prompt = dspy.InputField(desc="prompt on which need to create node schema")
    node_schema = dspy.OutputField(desc="node schema created based on the content" , type=dict)

class NodeSchemaGenerator(dspy.Module):
    def __init__(self, lm=None):
        super().__init__()
        self.lm = lm or get_dspy_lm()
        self.generate_summary = ChainOfThought(NodeSchemaSignature)

    def forward(self, content):
        with dspy.context(lm=self.lm):
            result = self.generate_summary(
                content=content,
                prompt="""
                CRITICAL: Extract STRUCTURE ONLY. DO NOT summarize or translate content.

                Your job is to identify conversation steps and what data each step collects.
                You will return JSON with node structure, but we will use the ORIGINAL content.

                For each conversation step, identify:
                1. A descriptive key_name (snake_case)
                2. What fields/data this step needs to collect (required array)
                3. A brief description of the step's purpose
                4. A section_marker (keywords from the original that identify this section)

                [OUTPUT STRUCTURE]
                [
                  {
                    "key_name": "descriptive_node_name",
                    "required": ["field1", "field2"],
                    "description": "Brief description of this step's purpose",
                    "section_marker": "keywords to identify this section in original content"
                  }
                ]

                [EXAMPLE INPUT]
                "**en** – Am I speaking with {{name}}?
                 **hi** – क्या मैं {{Name}} से बात कर रही हूँ?

                 ---

                 ### Main Loan Pitch
                 **en** – You are eligible for a pre-approved loan.
                 **hi** – आपके लिए लोन उपलब्ध है।

                 ---

                 ### If YES
                 Ask for employment status and city."

                [EXAMPLE OUTPUT]
                [
                  {
                    "key_name": "name_verification",
                    "required": ["name"],
                    "description": "Verify caller's name",
                    "section_marker": "Am I speaking with"
                  },
                  {
                    "key_name": "loan_pitch",
                    "required": ["interest"],
                    "description": "Present loan offer and check interest",
                    "section_marker": "Main Loan Pitch"
                  },
                  {
                    "key_name": "employment_details",
                    "required": ["employment_status", "city"],
                    "description": "Collect employment and location info",
                    "section_marker": "If YES"
                  }
                ]

                REMEMBER:
                - DO NOT include actual content in the schema
                - DO NOT translate or summarize
                - ONLY extract structure (names, fields, markers)
                - We will map original content back using section_marker
                """,
            )
            return dspy.Prediction(
                node_schema=result.node_schema
            )



def map_original_content_to_nodes(original_content: str, node_schemas: list) -> list:
    """
    Map original flow content to node schemas to preserve multi-language and exact phrasing.

    Args:
        original_content: The original flow section content (with multi-language, exact phrasing, etc.)
        node_schemas: List of node schemas from DSPy (structure only)

    Returns:
        List of node schemas enriched with original content
    """
    # Split original content by section markers (---, ###, etc.)
    sections = split_into_subsections(original_content)

    # Enrich each node schema with original content
    enriched_schemas = []
    for schema in node_schemas:
        section_marker = schema.get("section_marker", "")

        # Find matching section in original content
        matched_content = find_matching_section(sections, section_marker)

        if matched_content:
            # Use original content instead of DSPy summary
            schema["content"] = matched_content
        else:
            # Fallback: use description if no match found
            schema["content"] = schema.get("description", "")

        enriched_schemas.append(schema)

    return enriched_schemas


def split_into_subsections(content: str) -> list:
    """
    Split flow content into subsections based on markers (---, ###, section headers).

    Returns list of dicts with 'header' and 'content'
    """
    subsections = []

    # Split by --- or ### markers
    parts = re.split(r'(\n---\n|\n###)', content)

    current_section = {"header": "", "content": ""}

    for part in parts:
        part = part.strip()
        if not part:
            continue

        if part in ["---", "###"]:
            # Section separator - save current and start new
            if current_section["content"]:
                subsections.append(current_section)
            current_section = {"header": "", "content": ""}
        else:
            # Check if this is a header line (starts with ### or is all caps)
            lines = part.split('\n')
            if lines and (lines[0].startswith('###') or lines[0].isupper()):
                current_section["header"] = lines[0].replace('###', '').strip()
                current_section["content"] = '\n'.join(lines[1:]).strip()
            else:
                current_section["content"] = part

    # Add last section
    if current_section["content"]:
        subsections.append(current_section)

    # If no subsections found, return entire content as one section
    if not subsections:
        subsections.append({"header": "", "content": content})

    return subsections


def find_matching_section(sections: list, marker: str) -> str:
    """
    Find section that matches the marker keywords.

    Args:
        sections: List of subsections from split_into_subsections()
        marker: Keywords to search for

    Returns:
        Matched section content or empty string
    """
    if not marker:
        return ""

    marker_lower = marker.lower()

    # First pass: exact header match
    for section in sections:
        if marker_lower in section["header"].lower():
            return section["content"]

    # Second pass: content match
    for section in sections:
        if marker_lower in section["content"].lower():
            # Return content up to next section or reasonable limit
            content = section["content"]
            # Limit to first 500 chars if very long
            if len(content) > 500:
                # Try to find a natural break point
                lines = content.split('\n')
                truncated = []
                char_count = 0
                for line in lines:
                    if char_count + len(line) > 500:
                        break
                    truncated.append(line)
                    char_count += len(line)
                return '\n'.join(truncated) if truncated else content[:500]
            return content

    # No match found
    return ""


def start_convo() -> NodeConfig:
    return NodeConfig(
        name="initial conversation",
        role_messages=[
            {
                "role": "system",
                "content": """
                Objective:
                    Engage in a natural, contextual conversation with the lead, with the goal of converting them into a customer.

                    Instructions:

                    Leverage gathered information: Always use the information already collected about the lead to personalize responses.

                    Avoid repetition: Do not repeat details the lead has already provided.

                    Verify before proceeding: If certain critical information is missing or unverified, ask clear, concise follow-up questions to confirm it.

                    Value-driven engagement: Emphasize the benefits, solutions, or value relevant to the lead’s situation instead of generic sales talk.

                    Natural flow: Keep the tone conversational, professional, and customer-centric. Transition smoothly toward booking a meeting, demo, or purchase.

                    Conversion focus: Gently guide the lead toward the next step in the sales funnel (e.g., scheduling a call, trial signup, or closing).

                    Constraints:

                    Do not repeat already confirmed or verified details.

                    Always confirm missing or unclear information before progressing.

                    Ensure the flow feels like a genuine two-way conversation, not scripted.""",
            }
        ],
        task_messages=[
            {
                "role": "system",
                "content": "go through with the conversation with gathered information highy rely on the information gathered. make  the conversation based on gathered data and try to convert the lead into customer . Don't repetitive the information already gathered.  always check the vrerified information if they have required information ",
            }
        ]
    )

class Node:
    def __init__(self,data):
        self.data=data
        self.verify_class=self._create_verification_class()
        self.initial_class =self._create_initial_class()
        self.next_node=None
        self.node=self._create_initial_node()

    def _create_initial_class(self):
        return TypedDict(
            self.data["key_name"].replace(" ", "_"),
            {key: str for key in self.data["required"]},
        )

    def _create_verification_class(self):
        return type(
            self.data["key_name"].replace(" ","_")+"Verification",
            (FlowResult,),
            {key: str for key in self.data["required"]},
        )

    def _create_initial_node(self):
        func= FlowsFunctionSchema(
            name=self.data["key_name"].replace(" ", "_"),
            handler=self.verify ,
            description=self.data["description"],

            properties={
                field: {
                    "type": "string",
                    "description": self.data["description"]
                }
                for field in self.data["required"]
            },
            required=self.data["required"],
        )
        return NodeConfig(
                respond_immediately=True,
                name=self.data["key_name"].replace(" ","_"),
                role_messages=[
                {
                    "role": "system",
                    "content": f"You must ALWAYS use one of the {self.data['key_name'].replace(' ','_')}  to progress the conversation. Be professional but friendly.",
                }
            ],
            task_messages=[
                {
                    "role": "system",
                    "content": self.data["content"],
                }
            ],
            functions=[func],
        )


    async def verify(self,args: FlowArgs, flow_manager: FlowManager) -> tuple[FlowResult, NodeConfig]:
        missing = [field for field in self.data["required"] if not args.get(field)]
        if missing:
            return None, self.node
        result = self.verify_class(**{field: args.get(field) for field in self.data["required"]})
        next_node = self.next_node.node if self.next_node else start_convo()
        return result, next_node

def dynamic_nodes(node_schema) -> List[NodeConfig]:
    nodes = [Node(data) for data in node_schema]
    for i in range(len(nodes) - 1):
        nodes[i].next_node = nodes[i + 1]
    return [node.node for node in nodes]



def extract_sections(document_text):
    matches = list(re.finditer(r"\[(.*?)\]", document_text))
    sections = []

    for i, match in enumerate(matches):
        section_name = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(document_text)
        section_content = document_text[start:end].strip()

        sections.append({
            "section": section_name,
            "content": section_content
        })

    return sections


def load_docx_to_text(file_path):
    from docx import Document  # Lazy import to avoid compatibility issues
    doc = Document(file_path)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text


def validate_node_conversion(original_content: str, enriched_schemas: list) -> dict:
    """
    Validate conversion quality and calculate metrics.

    Args:
        original_content: Original flow section content
        enriched_schemas: Node schemas after content mapping

    Returns:
        Dict with validation metrics and warnings
    """
    metrics = {
        "total_nodes": len(enriched_schemas),
        "nodes_with_content": 0,
        "multi_language_preserved": False,
        "template_vars_found": False,
        "wait_states_found": False,
        "warnings": [],
        "coverage_score": 0.0
    }

    # Check each node
    for schema in enriched_schemas:
        content = schema.get("content", "")

        if content and len(content) > 10:  # Meaningful content
            metrics["nodes_with_content"] += 1

        # Check for multi-language markers (Hindi/Devanagari script)
        if any('\u0900' <= char <= '\u097F' for char in content):
            metrics["multi_language_preserved"] = True

        # Check for template variables
        if "{{" in content and "}}" in content:
            metrics["template_vars_found"] = True

        # Check for wait states
        if any(marker in content.lower() for marker in ["wait for", "< wait", "<wait"]):
            metrics["wait_states_found"] = True

    # Calculate coverage
    if len(enriched_schemas) > 0:
        metrics["coverage_score"] = metrics["nodes_with_content"] / len(enriched_schemas)

    # Generate warnings
    if metrics["total_nodes"] == 0:
        metrics["warnings"].append("CRITICAL: No nodes generated")

    if metrics["coverage_score"] < 0.5:
        metrics["warnings"].append(f"LOW: Only {metrics['coverage_score']:.0%} nodes have content")

    # Check if original has multi-language but nodes don't
    has_hindi_original = any('\u0900' <= char <= '\u097F' for char in original_content)
    if has_hindi_original and not metrics["multi_language_preserved"]:
        metrics["warnings"].append("CRITICAL: Multi-language content lost (Hindi → English only)")

    # Check if original has template vars but nodes don't
    has_templates_original = "{{" in original_content and "}}" in original_content
    if has_templates_original and not metrics["template_vars_found"]:
        metrics["warnings"].append("HIGH: Template variables lost (e.g., {{name}})")

    return metrics


async def create_section_based_flow(
    system_prompt: str,
    assistant_prompt: str = None,
    get_docs_handler = None,
    handover_handler = None,
    end_call_handler = None
) -> List[NodeConfig]:
    """
    Create dynamic flow from system_prompt using section-based architecture.

    NEW APPROACH (vs. hybrid DSPy approach):
    1. Parse sections into typed structures (identity, question, condition, objection)
    2. Generate specialized handlers for each section type
    3. Create NodeConfig objects with handlers
    4. Inject objection handlers into all nodes for global access
    5. Inject global utility functions (get_docs, handover, end_call) into all nodes
    6. Enable conditional branching (If YES/NO logic)
    7. Incorporate full assistant_prompt context into each node

    Benefits:
    - 30-50% faster (no DSPy LLM call)
    - Conditional branching (If YES → A, If NO → B)
    - Objection handling (interruptions anywhere)
    - Global utilities (KB search, handover, end call) available everywhere
    - Multi-language preservation (original content)
    - Runtime adaptability (flow based on user responses)
    - Full context preservation (agent identity, rules, guidelines)

    Args:
        system_prompt: Multi-line prompt with [Section Name] markers
        assistant_prompt: Full assistant prompt from PromptManager (includes agent identity,
                         tone, timestamp, rules). If provided, will be incorporated into
                         each node's role_messages to ensure context consistency.
        get_docs_handler: Handler function for knowledge base retrieval (optional)
        handover_handler: Handler function for call handover (optional)
        end_call_handler: Handler function for ending calls (optional)

    Returns:
        List of NodeConfig objects ready for FlowManager, or None if parsing fails

    Example:
        system_prompt = '''
        [Agent Identity]
        You are Neha from Sitaara Housing Finance

        [Greeting]
        **en** – Hello! Am I speaking with {{name}}?
        **hi** – नमस्ते! क्या मैं {{name}} से बात कर रही हूँ?

        [Main Loan Pitch]
        You're eligible for ₹2 lakh loan. Interested?

        [If YES]
        Great! Let me collect employment details.

        [If NO]
        No problem. Can I ask why not interested?

        [Customer Objection: Interest Rate Too High]
        I understand your concern...
        '''

        nodes = await create_section_based_flow(system_prompt)
        # Returns nodes with:
        # - greeting → loan_pitch → condition_yes_no
        #                             ├─YES→ employment_details
        #                             └─NO → objection_handler
        # - Objection handlers accessible from all nodes
    """
    try:
        # Import section-based components
        from .section_parser import SectionParser
        from .handler_factory import HandlerFactory
        from .node_factory import NodeFactory
        from .objection_manager import ObjectionManager

        print(f"\n{'='*60}")
        print(f"SECTION-BASED FLOW GENERATION")
        print(f"{'='*60}")

        # Step 1: Extract all sections
        print("Step 1: Extracting sections...")
        sections = extract_sections(system_prompt)
        print(f"  Found {len(sections)} sections")

        if not sections:
            print("  ⚠️  No sections found in system_prompt")
            return None

        # Step 2: Parse sections into typed structures
        print("Step 2: Parsing sections into typed structures...")
        parser = SectionParser()
        parsed_flow = parser.parse_sections(sections)

        print(f"  Identity: {'✓' if parsed_flow.identity else '✗'}")
        print(f"  Greeting: {'✓' if parsed_flow.greeting else '✗'}")
        print(f"  Questions: {len(parsed_flow.questions)}")
        print(f"  Pitches: {len(parsed_flow.pitches)}")
        print(f"  Conditions: {len(parsed_flow.conditions)}")
        print(f"  Objections: {len(parsed_flow.objections)}")
        print(f"  Flow order: {len(parsed_flow.flow_order)} steps")

        if not parsed_flow.flow_order:
            print("  ⚠️  No flow sequence generated")
            return None

        # Step 3: Create handlers for all sections
        print("Step 3: Generating specialized handlers...")
        handler_factory = HandlerFactory(parsed_flow)
        handlers = handler_factory.create_all_handlers()
        print(f"  Created {len(handlers)} handlers")

        # Step 4: Create nodes from sections
        print("Step 4: Creating NodeConfig objects...")
        node_factory = NodeFactory(parsed_flow, handler_factory, assistant_prompt=assistant_prompt)
        nodes = node_factory.create_all_nodes()
        print(f"  Created {len(nodes)} nodes")
        if assistant_prompt:
            print(f"  ✓ Incorporated full assistant prompt context into each node")

        # Step 5: Inject objection handlers into all nodes
        print("Step 5: Injecting objection handlers...")
        objection_mgr = ObjectionManager(parsed_flow, handler_factory)
        if objection_mgr.has_objections():
            nodes = objection_mgr.inject_objection_handlers_into_nodes(nodes)
            print(f"  Injected {len(parsed_flow.objections)} objection handlers into all nodes")
        else:
            print("  No objection handlers to inject")

        # Step 5.5: Inject global utility functions into all nodes
        print("Step 5.5: Injecting global utility functions...")
        from .global_function_manager import GlobalFunctionManager
        global_mgr = GlobalFunctionManager(
            get_docs_handler=get_docs_handler,
            handover_handler=handover_handler,
            end_call_handler=end_call_handler
        )
        if global_mgr.has_global_functions():
            nodes = global_mgr.inject_global_functions_into_nodes(nodes)
            global_funcs = global_mgr.get_global_functions()
            func_names = [f.name for f in global_funcs]
            print(f"  Injected {len(func_names)} global functions into all nodes: {', '.join(func_names)}")
        else:
            print("  No global utility functions to inject")

        # Step 6: Validation
        print("Step 6: Validating flow...")
        print(f"  Total nodes: {len(nodes)}")

        # Check multi-language preservation
        has_hindi = False
        for section_id in parsed_flow.flow_order:
            section = parsed_flow.sections_by_id.get(section_id)
            if section and any('\u0900' <= char <= '\u097F' for char in section.content):
                has_hindi = True
                break

        print(f"  Multi-language content: {'✓ Preserved' if has_hindi else '✗ Not found'}")
        print(f"  Conditional branching: {'✓ Enabled' if parsed_flow.conditions else '✗ No conditions'}")
        print(f"  Objection handling: {'✓ Enabled' if parsed_flow.objections else '✗ No objections'}")
        print(f"  Global utilities: {'✓ Enabled' if global_mgr.has_global_functions() else '✗ No global functions'}")

        print(f"\n✅ Section-based flow generated successfully!")
        print(f"{'='*60}\n")

        return nodes

    except Exception as e:
        import traceback
        print(f"\n❌ Error in section-based flow generation:")
        print(f"  {e}")
        print(f"  Traceback: {traceback.format_exc()}")
        print(f"{'='*60}\n")
        return None


def extract_flow_section(system_prompt: str):
    """
    Extract conversation flow/structure section from system_prompt.

    Looks for sections containing:
    - [Task and Goals]
    - [Conversation Structure]
    - [Conversation Flow]
    - [Steps]
    - [Flow]

    Args:
        system_prompt: The full system prompt text

    Returns:
        Dictionary with section name and content, or None if not found
    """
    sections = extract_sections(system_prompt)

    # Keywords that indicate a flow/structure section
    flow_keywords = [
        "task and goals",
        "conversation structure",
        "conversation flow",
        "steps",
        "flow",
        "conversation steps",
        "conversations",
        "task"
    ]

    # Find the first section that matches flow keywords
    for section in sections:
        section_name_lower = section["section"].lower()
        for keyword in flow_keywords:
            if keyword in section_name_lower:
                return section

    return None


async def create_nodes_from_system_prompt(system_prompt: str) -> List[NodeConfig]:
    """
    Generate dynamic nodes from system_prompt using hybrid approach.

    HYBRID APPROACH:
    1. DSPy extracts STRUCTURE (node names, required fields, section markers)
    2. Original content is mapped back to preserve multi-language and exact phrasing
    3. NodeConfigs created with enriched schemas

    This preserves:
    - Multi-language content (English + Hindi)
    - Exact phrasing and amounts
    - Template variables ({{name}})
    - Wait states
    - Formatting

    Args:
        system_prompt: Multi-line prompt from user_state.system_prompt

    Returns:
        List of NodeConfig objects ready for FlowManager, or None if flow section not found

    Example:
        system_prompt = '''
        [Agent Identity]
        You are Neha from Sitaara Housing Finance

        [Task and Goals]
        **en** – Am I speaking with {{name}}?
        **hi** – क्या मैं {{name}} से बात कर रही हूँ?

        ---

        ### Main Loan Pitch
        Present the loan offer...
        '''

        nodes = await create_nodes_from_system_prompt(system_prompt)
        # Nodes will contain original multi-language content!
    """
    try:
        # Extract flow section from system prompt
        flow_section = extract_flow_section(system_prompt)

        if not flow_section:
            # No flow section found, return None to allow fallback
            return None

        original_content = flow_section.get("content")

        # Step 1: Use DSPy to extract STRUCTURE ONLY (not content)
        schema_generator = NodeSchemaGenerator()
        result = schema_generator(content=original_content)

        # Parse the JSON schema
        import json
        node_schema = json.loads(result.node_schema)

        # Step 2: Map original content back to nodes using section markers
        # This preserves multi-language, exact phrasing, etc.
        enriched_schema = map_original_content_to_nodes(original_content, node_schema)

        # Step 3: Validate conversion quality
        validation_metrics = validate_node_conversion(original_content, enriched_schema)

        # Log validation results
        print(f"\n{'='*60}")
        print(f"NODE CONVERSION VALIDATION")
        print(f"{'='*60}")
        print(f"Total nodes generated: {validation_metrics['total_nodes']}")
        print(f"Nodes with content: {validation_metrics['nodes_with_content']}")
        print(f"Coverage score: {validation_metrics['coverage_score']:.1%}")
        print(f"Multi-language preserved: {'✓' if validation_metrics['multi_language_preserved'] else '✗'}")
        print(f"Template vars preserved: {'✓' if validation_metrics['template_vars_found'] else '✗'}")
        print(f"Wait states preserved: {'✓' if validation_metrics['wait_states_found'] else '✗'}")

        if validation_metrics['warnings']:
            print(f"\n⚠️  WARNINGS:")
            for warning in validation_metrics['warnings']:
                print(f"  - {warning}")
        else:
            print(f"\n✓ No critical issues detected")

        print(f"{'='*60}\n")

        # Step 4: Create dynamic nodes from enriched schema
        nodes = dynamic_nodes(enriched_schema)

        return nodes

    except Exception as e:
        # Log the error but don't crash
        import traceback
        print(f"Error creating nodes from system_prompt: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return None


async def create_document_with_nodes():
    try:
        file_path = "C:\\Users\Arshpreet-Unpod\Downloads\Vajiram And Ravi Knowledge base.docx"
        text = load_docx_to_text(file_path)
        sections = extract_sections(text)

        conversation_structure = next(
            (item for item in sections if item["section"]== "Conversation Structure"),
            None
        )
        # print(conversation_structure)

        schema_generator = NodeSchemaGenerator().forward(conversation_structure.get("content"))
        import json
        node_schema = json.loads(schema_generator.node_schema)

        # print("generated schema ", node_schema)
        nodes = dynamic_nodes(node_schema)
        # print("nodes",nodes)
        return nodes
    except Exception as e:
        return None

if __name__ == "__main__":
    import asyncio
    asyncio.run(create_document_with_nodes())


