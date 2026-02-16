"""
ReAct Node Builder V2 - Simplified Think-Based Architecture with Communication

This module implements a simplified ReAct pattern where Think nodes handle everything:

**Think Node** (Main conversational node):
- Has FULL context (instructions + identity + objections + state)
- Has ALL functions available (search, handover, end_call, goal collection)
- Can communicate AND execute functions in one turn
- Provides user-friendly feedback for time-consuming actions
- Workflow: Brief "please wait" → Call function → Use result → Continue conversation

**Example Turn (Time-consuming action)**:
User: "What courses do you offer?"
Think:
  1. Outputs: "Let me search for our course offerings..." (TTS - user feedback)
  2. Calls: search_docs("courses")
  3. Receives: [course list results]
  4. Outputs: "We offer UPSC Foundation, Mains Guidance..." (TTS - results)
  5. Waits for user input

**Example Turn (Quick interaction)**:
User: "My name is Raj"
Think:
  1. Outputs: "Nice to meet you, Raj!" (TTS)
  2. Calls: collect_user_name("Raj") (silently)
  3. Waits for user input

**Key Principles**:
- Time-consuming actions (search, API calls): Brief user feedback before execution
- Quick interactions (collecting info): Natural response without announcements
- Never announce internal reasoning or meta-commentary

**Optional Node Types** (for specialized scenarios):
- Talk: Pure communication (minimal context, NO functions)
- Act: Dedicated function execution (currently unused in simplified model)

The simplified V2 architecture eliminates the need for separate Act nodes since
Think nodes can execute functions directly while maintaining conversational flow.
"""

from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field

try:
    from pipecat_flows import NodeConfig, FunctionConfig
    from pipecat.frames.frames import LLMMessagesFrame, EndFrame
    from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
except ImportError:
    # Fallback types for development
    NodeConfig = dict
    FunctionConfig = dict
    LLMMessagesFrame = object
    EndFrame = object
    OpenAILLMContext = object


@dataclass
class FunctionRegistry:
    """
    Central registry of ALL available functions.

    Think nodes get ALL functions so they can decide anything.
    Act nodes get ONLY the specific function they need to execute.

    Functions are stored as FlowsFunctionSchema objects from pipecat_flows.
    """
    search_docs: Optional[Any] = None  # FlowsFunctionSchema
    handover: Optional[Any] = None      # FlowsFunctionSchema
    end_call: Optional[Any] = None      # FlowsFunctionSchema
    goal_functions: Dict[str, Any] = field(default_factory=dict)  # func_name -> FlowsFunctionSchema

    def get_all_functions(self) -> List[Any]:
        """
        Get ALL functions for Think node.

        Returns:
            List of FlowsFunctionSchema objects
        """
        functions = []

        if self.search_docs:
            functions.append(self.search_docs)
        if self.handover:
            functions.append(self.handover)
        if self.end_call:
            functions.append(self.end_call)

        # Add all goal collection functions
        functions.extend(self.goal_functions.values())

        return functions

    def get_function(self, function_name: str) -> Optional[Any]:
        """
        Get specific function for Act node.

        Returns:
            FlowsFunctionSchema object or None
        """
        # Check standard functions
        if function_name == "search_docs" and self.search_docs:
            return self.search_docs
        if function_name == "handover" and self.handover:
            return self.handover
        if function_name == "end_call" and self.end_call:
            return self.end_call

        # Check goal functions
        return self.goal_functions.get(function_name)

    def add_goal_function(self, function_config: Any):
        """
        Add a goal collection function to registry.

        Args:
            function_config: FlowsFunctionSchema object (or dict for backward compatibility)
        """
        # Handle both FlowsFunctionSchema objects and dicts
        if isinstance(function_config, dict):
            func_name = function_config.get("name", "")
        else:
            func_name = getattr(function_config, "name", "")

        if func_name:
            self.goal_functions[func_name] = function_config


class ReActNodeBuilderV2:
    """
    Builder for creating Think-Talk-Act node triads.

    Each turn consists of:
    1. Think (decision) → 2. Talk (communication) → 3. Act (execution) → back to Think
    """

    def __init__(
        self,
        instructions: str,
        identity: str,
        objections: Dict[str, str],
        function_registry: FunctionRegistry,
        observation_state: Optional[Any] = None
    ):
        """
        Initialize ReAct node builder V2.

        Args:
            instructions: Full instructions text
            identity: Agent identity/persona
            objections: Map of objection_id -> content
            function_registry: Registry of all available functions
            observation_state: ObservationState instance
        """
        self.instructions = instructions
        self.identity = identity
        self.objections = objections
        self.function_registry = function_registry
        self.observation_state = observation_state

    def build_think_node(
        self,
        node_id: str,
        available_actions: List[str],
        current_state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build Think node for decision making AND user communication.

        Think nodes:
        - Have FULL context (instructions + identity + objections + state)
        - Have ALL functions registered (can decide any action)
        - Can output conversational text (goes to TTS)
        - Communicate to user what they're doing before executing action
        - Output: Conversational message + decides next action

        Args:
            node_id: Unique node identifier
            available_actions: List of available action names
            current_state: Current conversation state

        Returns:
            NodeConfig dict for Think node
        """
        # Build full context for decision making
        role_message = self._build_think_role(current_state)

        # Build task for decision + communication
        task_message = self._build_think_task(available_actions, current_state)

        # Get ALL functions (Think has access to all actions)
        all_functions = self.function_registry.get_all_functions()

        think_node = {
            "name": f"think_{node_id}",
            "role_messages": [{"role": "system", "content": role_message}],
            "task_messages": [{"role": "user", "content": task_message}],
            "functions": all_functions,  # ALL functions registered
            "pre_actions": [],
            "post_actions": [],
            "metadata": {
                "node_type": "think",
                "has_full_context": True,
                "can_talk": True,  # Can output to TTS
                "available_actions": available_actions
            }
        }

        return think_node

    def build_talk_node(
        self,
        action_name: str,
        action_description: str,
        next_node: str
    ) -> Dict[str, Any]:
        """
        Build Talk node for user communication.

        Talk nodes:
        - Have MINIMAL context (just identity + current goal)
        - Have NO functions (pure conversational output)
        - Speak to user about what's happening (goes to TTS)
        - Output: Conversational text like "Let me check that for you..."

        Args:
            action_name: Name of action being communicated
            action_description: Human-readable description
            next_node: Next node to transition to

        Returns:
            NodeConfig dict for Talk node
        """
        # Minimal context for speech
        role_message = self._build_talk_role()

        # Task: communicate action to user
        task_message = self._build_talk_task(action_name, action_description)

        talk_node = {
            "name": f"talk_{action_name}",
            "role_messages": [{"role": "system", "content": role_message}],
            "task_messages": [{"role": "user", "content": task_message}],
            "functions": [],  # NO functions - pure speech
            "pre_actions": [],
            "post_actions": [],
            "metadata": {
                "node_type": "talk",
                "action_being_communicated": action_name,
                "next_node": next_node
            }
        }

        return talk_node

    def build_act_node(
        self,
        function_name: str,
        next_node: str
    ) -> Dict[str, Any]:
        """
        Build Act node for function execution.

        Act nodes:
        - Have NO context (no LLM call needed)
        - Have ONE specific function (the one to execute)
        - Execute function and update state
        - Output: Function result

        Args:
            function_name: Name of function to execute
            next_node: Next node to transition to (usually think)

        Returns:
            NodeConfig dict for Act node
        """
        # Get the specific function from registry
        function_config = self.function_registry.get_function(function_name)

        if not function_config:
            raise ValueError(f"Function {function_name} not found in registry")

        act_node = {
            "name": f"act_{function_name}",
            "role_messages": [],  # No LLM call needed
            "task_messages": [],  # Function execution only
            "functions": [function_config],  # ONLY this function
            "pre_actions": [],
            "post_actions": [],
            "metadata": {
                "node_type": "act",
                "function_name": function_name,
                "next_node": next_node
            }
        }

        return act_node

    # ==================== Context Builders ====================

    def _build_think_role(self, current_state: Optional[Dict[str, Any]] = None) -> str:
        """
        Build FULL context for Think node.

        Includes everything needed for intelligent decision making.
        """
        parts = []

        # Full instructions
        if self.instructions:
            parts.append(f"**Instructions:**\\n{self.instructions}")

        # Full identity
        if self.identity:
            parts.append(f"**Your Identity:**\\n{self.identity}")

        # Objections knowledge
        if self.objections:
            objections_text = "\\n\\n".join(
                f"**{obj_id}:**\\n{content}"
                for obj_id, content in self.objections.items()
            )
            parts.append(f"**Objection Handling:**\\n{objections_text}")

        # Current state
        if current_state:
            state_text = self._format_state(current_state)
            parts.append(f"**Current State:**\\n{state_text}")

        return "\\n\\n---\\n\\n".join(parts)

    def _build_think_task(
        self,
        available_actions: List[str],
        current_state: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build task for Think node - natural conversation with function calling."""
        # Allow brief user-friendly messages for time-consuming actions
        # But avoid announcing internal reasoning or every function call

        state_summary = ""
        if current_state:
            state_summary = f"\\n\\n**Current Progress:**\\n{self._format_state(current_state)}"

        task = f"""**Respond Naturally and Keep Users Informed**

Engage in a natural conversation with the user to help them with their queries.

{state_summary}

**Guidelines for Function Calling**:

1. **Time-consuming actions** (search, lookups, database queries):
   - Briefly inform user before calling: "Let me search for that information..." or "One moment while I check..."
   - Then call the function
   - Then respond with the results

2. **Quick interactions** (collecting user info, simple responses):
   - Just respond naturally without announcing actions
   - Example: User asks for name → You just collect it naturally

3. **Keep responses concise** and focused on helping the user

**Examples**:

Good (time-consuming action):
- User: "What courses do you offer?"
- You: "Let me search for our course offerings..." *calls search_docs("courses")* "We offer UPSC Foundation, Mains Guidance..."

Good (quick interaction):
- User: "My name is Raj"
- You: "Nice to meet you, Raj!" *calls collect_user_name naturally*

Bad (announcing internal reasoning):
- NOT: "I'm going to confirm whether all your questions have been addressed"
- NOT: "Let me think about what to do next..."
"""
        return task

    def _build_talk_role(self) -> str:
        """
        Build MINIMAL context for Talk node.

        Just enough to maintain persona in speech.
        """
        # Just the first line of identity (e.g., "You are Saanvi from Vajiram & Ravi")
        if self.identity:
            identity_short = self.identity.split('\\n')[0]
            return identity_short

        return "You are a helpful assistant."

    def _build_talk_task(self, action_name: str, action_description: str) -> str:
        """Build task for Talk node."""
        task = f"""**Communicate with User**

You are about to: {action_description}

Before proceeding, briefly inform the user what you're doing. Be natural and conversational.

Examples:
- "Let me check that information for you..."
- "I'm looking up the course details now..."
- "Give me a moment to find that..."

Keep it concise (1 sentence) and maintain your warm, friendly tone.
"""
        return task

    def _format_state(self, state: Dict[str, Any]) -> str:
        """Format state dict into readable text."""
        parts = []

        if "current_goal" in state:
            parts.append(f"Current Goal: {state['current_goal']}")

        if "collected_fields" in state and state["collected_fields"]:
            fields_str = ", ".join(
                f"{k}={v}" for k, v in state["collected_fields"].items()
            )
            parts.append(f"Collected: {fields_str}")

        if "pending_goals" in state and state["pending_goals"]:
            parts.append(f"Pending Goals: {len(state['pending_goals'])}")

        if "completed_goals" in state and state["completed_goals"]:
            parts.append(f"Completed: {len(state['completed_goals'])}")

        return " | ".join(parts) if parts else "No state yet"

    # ==================== Function Builders ====================

    def _create_decide_action_function(self, available_actions: List[str]) -> Dict[str, Any]:
        """
        Create function for Think node to decide next action.

        Returns action name via function call (silent - no TTS).
        """
        function_config = {
            "name": "decide_next_action",
            "description": "Choose the next action to take in the conversation",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": available_actions,
                        "description": "The next action to execute"
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "Brief explanation of why this action was chosen"
                    }
                },
                "required": ["action"]
            }
        }

        return function_config


# ==================== Flow Converter ====================

class ReActFlowConverterV2:
    """
    Converts standard nodes into simplified Think-based flow.

    Creates a single Think node that:
    - Has ALL functions registered (from standard nodes + core functions)
    - Handles communication AND function execution
    - Maintains full context for intelligent decision making
    - Waits for user input after each turn

    No separate Act nodes are created since Think handles function execution directly.
    """

    def __init__(self, builder: ReActNodeBuilderV2):
        """
        Initialize converter with a builder instance.

        Args:
            builder: ReActNodeBuilderV2 instance with all context and functions
        """
        self.builder = builder
        self.node_counter = 0

    def convert_standard_nodes_to_react(
        self,
        standard_nodes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Convert standard nodes into simplified V2 ReAct flow.

        Creates a single Think node with all functions available.
        Think node handles both communication and function execution.

        Args:
            standard_nodes: List of standard node configs

        Returns:
            List containing single Think node (simplified V2 architecture)
        """
        react_nodes = []

        # Extract all action names from standard nodes
        action_names = self._extract_action_names(standard_nodes)

        # Create single Think node with ALL functions
        # This node handles:
        # 1. Communication with user
        # 2. Function calling (search, handover, goal collection, etc.)
        # 3. State management
        # 4. Waiting for user input
        entry_think = self.builder.build_think_node(
            node_id="entry",
            available_actions=action_names,
            current_state=None
        )
        react_nodes.append(entry_think)

        # Note: No Act nodes created in simplified V2
        # All functions execute within the Think node
        # Think node has all functions registered via FunctionRegistry

        return react_nodes

    def _extract_action_names(self, nodes: List[Dict[str, Any]]) -> List[str]:
        """Extract all available action names from nodes."""
        actions = []

        for node in nodes:
            functions = node.get("functions", [])
            for func in functions:
                if isinstance(func, dict):
                    func_name = func.get("name", "")
                else:
                    func_name = getattr(func, "name", "")

                if func_name and func_name not in actions:
                    # Filter out internal functions
                    if func_name not in ["decide_next_action"]:
                        actions.append(func_name)

        return actions

    def _get_function_name(self, functions: List[Any]) -> Optional[str]:
        """Get the primary function name from a functions list."""
        if not functions:
            return None

        func = functions[0]  # Take first function

        if isinstance(func, dict):
            return func.get("name", "")
        else:
            return getattr(func, "name", "")


# ==================== Helper Functions ====================

def create_think_act_pair(
    builder: ReActNodeBuilderV2,
    node_id: str,
    available_actions: List[str],
    function_name: str,
    current_state: Optional[Dict[str, Any]] = None
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Create a Think → Act pair for one turn.

    Args:
        builder: ReActNodeBuilderV2 instance
        node_id: Unique identifier for this pair
        available_actions: List of available actions for Think
        function_name: Function to execute in Act
        current_state: Current conversation state

    Returns:
        Tuple of (think_node, act_node)
    """
    # 1. Think node - decides what to do + tells user
    think_node = builder.build_think_node(
        node_id=node_id,
        available_actions=available_actions,
        current_state=current_state
    )

    # 2. Act node - executes the function
    act_node = builder.build_act_node(
        function_name=function_name,
        next_node=f"think_{node_id}"  # Loop back to Think
    )

    return think_node, act_node
