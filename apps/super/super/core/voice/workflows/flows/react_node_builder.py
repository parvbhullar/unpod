"""
ReAct Node Builder - Creates Think, Act, and Observe nodes.

This module provides builders for creating ReAct-optimized conversation nodes
that work with Pipecat's NodeConfig structure.
"""

from typing import Any, Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass

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


class ReActNodeBuilder:
    """
    Builder for creating ReAct-optimized nodes (Think, Act, Observe).

    Converts standard flow nodes into a three-phase ReAct loop:
    1. Think: Reasoning with full context
    2. Act: Focused action execution
    3. Observe: Result tracking and state management
    """

    def __init__(
        self,
        instructions: str,
        identity: str,
        objections: Dict[str, str],
        observation_state: Optional[Any] = None
    ):
        """
        Initialize ReAct node builder.

        Args:
            instructions: Combined instructions text
            identity: Agent identity/persona
            objections: Map of objection_id -> content
            observation_state: ObservationState instance
        """
        self.instructions = instructions
        self.identity = identity
        self.objections = objections
        self.observation_state = observation_state

    def build_think_node(
        self,
        node_id: str,
        next_action: str,
        available_actions: List[str]
    ) -> Dict[str, Any]:
        """
        Build a Think node for reasoning about next action.

        Think nodes:
        - Have full context (instructions + identity + objections)
        - Include observation summary
        - Use function call to decide next action (SILENT - no TTS)

        Args:
            node_id: Unique node identifier
            next_action: Default next action
            available_actions: List of available action names

        Returns:
            NodeConfig dict
        """
        # Build think task message
        task_message = self._build_think_task(available_actions)

        # Build role message with full context
        role_message = self._build_think_role()

        # Create decision function (SILENT - prevents TTS of action names)
        decide_function = self._create_decide_action_function(available_actions, next_action)

        # Create node config
        node = {
            "name": f"think_{node_id}",
            "role_messages": [{"role": "system", "content": role_message}],
            "task_messages": [{"role": "user", "content": task_message}],
            "functions": [decide_function],  # Function captures decision silently
            "pre_actions": [],
            "post_actions": [],
            "metadata": {
                "node_type": "think",
                "has_full_context": True,
                "is_silent": True  # Mark as silent node
            }
        }

        return node

    def build_act_node(
        self,
        original_node: Dict[str, Any],
        action_type: str = "goal_collection"
    ) -> Dict[str, Any]:
        """
        Build an Act node for executing a specific action.

        Act nodes:
        - Have focused context (only what's needed for action)
        - Register specific function(s) ONLY for action nodes
        - Conversational nodes (goal_collection) have NO functions to ensure speech output

        Args:
            original_node: Original NodeConfig from flow generator
            action_type: Type of action (goal_collection, search, handover, end)

        Returns:
            Modified NodeConfig for Act phase
        """
        # Handle both dict and NodeConfig objects
        if isinstance(original_node, dict):
            original_name = original_node.get("name", "unknown")
            functions = original_node.get("functions", [])
            pre_actions = original_node.get("pre_actions", [])
        else:
            original_name = getattr(original_node, "name", "unknown")
            functions = getattr(original_node, "functions", [])
            pre_actions = getattr(original_node, "pre_actions", [])

        # Build focused act context
        role_message = self._build_act_role()

        # Build act task (simplified from original)
        task_message = self._build_act_task(original_node, action_type)

        # CRITICAL FIX: Filter functions based on action type
        # Conversational nodes should NOT have functions (to enable speech)
        # Action nodes keep ONLY their specific function
        filtered_functions = self._filter_functions_for_action(functions, action_type)

        # Create act node
        act_node = {
            "name": f"act_{original_name}",
            "role_messages": [{"role": "system", "content": role_message}],
            "task_messages": [{"role": "user", "content": task_message}],
            "functions": filtered_functions,  # Filtered based on action_type
            "pre_actions": pre_actions,
            "post_actions": [],  # Move to observe node
            "metadata": {
                "node_type": "act",
                "original_node": original_name,
                "action_type": action_type
            }
        }

        return act_node

    def build_observe_node(
        self,
        action_name: str,
        next_node: str,
        required_fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Build an Observe node for tracking action results.

        Observe nodes are SILENT:
        - No LLM calls (would cause unwanted speech)
        - Just transition to next node
        - State tracking happens in ReActFlowManager

        Args:
            action_name: Name of action being observed
            next_node: Default next node
            required_fields: Required fields for goal completion

        Returns:
            NodeConfig dict
        """
        # Observe nodes should be silent - no messages, just transition
        # Use empty messages to avoid LLM call
        observe_node = {
            "name": f"observe_{action_name}",
            "role_messages": [],  # Empty = no LLM call
            "task_messages": [],  # Empty = no LLM call
            "functions": [],  # No functions needed for simple transition
            "pre_actions": [],
            "post_actions": [],
            "metadata": {
                "node_type": "observe",
                "observing_action": action_name,
                "next_node": next_node,
                "required_fields": required_fields or [],
                "is_silent": True  # Mark as silent
            }
        }

        return observe_node

    def _build_think_task(self, available_actions: List[str]) -> str:
        """Build task message for Think node."""
        obs_summary = ""
        if self.observation_state:
            obs_summary = f"\n\n**Current State:**\n{self.observation_state.to_context_summary()}"

        actions_list = "\n".join(f"- {action}" for action in available_actions)

        task = f"""**Internal Decision: Choose Next Action**

            Based on the conversation context and current state, use the decide_next_action function to select what to do next.
            {obs_summary}

            **Available Actions:**
            {actions_list}

            Analyze the situation silently and call decide_next_action with:
            - action: the chosen action name
            - reasoning: brief explanation of why

            DO NOT respond with text - use the function call only.
            """
        return task

    def _build_think_role(self) -> str:
        """Build role message for Think node with full context."""
        parts = []

        if self.instructions:
            parts.append(f"**Instructions:**\n{self.instructions}")

        if self.identity:
            parts.append(f"**Your Identity:**\n{self.identity}")

        if self.objections:
            objections_text = "\n\n".join(
                f"**{obj_id}:**\n{content}"
                for obj_id, content in self.objections.items()
            )
            parts.append(f"**Objection Handling:**\n{objections_text}")

        return "\n\n---\n\n".join(parts)

    def _build_act_role(self) -> str:
        """
        Build role message for Act node with essential context.

        IMPORTANT: Since we removed Think nodes, Act nodes need the full identity
        and core instructions to maintain the agent's persona and guidelines.
        """
        parts = []

        # Include full identity (not just first line)
        if self.identity:
            parts.append(self.identity)

        # Include core instructions for response style
        if self.instructions:
            # Include full instructions to maintain agent behavior
            parts.append(f"**Guidelines:**\n{self.instructions}")

        if parts:
            return "\n\n".join(parts)

        return "You are a helpful assistant."

    def _build_act_task(self, original_node: Dict[str, Any], action_type: str) -> str:
        """Build focused task message for Act node."""
        # Handle both dict and NodeConfig objects
        if isinstance(original_node, dict):
            original_tasks = original_node.get("task_messages", [])
        else:
            original_tasks = getattr(original_node, "task_messages", [])

        # Extract content from message dict
        original_task = ""
        if original_tasks:
            first_msg = original_tasks[0]
            if isinstance(first_msg, dict):
                original_task = first_msg.get("content", "")
            else:
                original_task = str(first_msg)

        # Simplify for focused execution
        if action_type == "goal_collection":
            collected = ""
            if self.observation_state and self.observation_state.collected_fields:
                fields_str = ", ".join(
                    f"{k}={v}" for k, v in self.observation_state.collected_fields.items()
                )
                collected = f"\n\n**Already collected:** {fields_str}"

            return f"""**Execute: Collect Information**

                {original_task}
                {collected}
                
                Ask the question naturally and collect the required information.
                """
        elif action_type == "search":
            return f"**Execute: Search Documentation**\n\n{original_task}"
        elif action_type == "handover":
            return f"**Execute: Handover to Agent**\n\n{original_task}"
        elif action_type == "end":
            return f"**Execute: End Conversation**\n\n{original_task}"
        else:
            return original_task

    def _build_observe_role(self) -> str:
        """Build minimal role for Observe node."""
        return "You are tracking conversation state."

    def _build_observe_task(self, required_fields: List[str]) -> str:
        """Build task for Observe node."""
        if required_fields:
            fields_list = ", ".join(required_fields)
            return f"""**Observe: Extract Information**
                From the last exchange, extract the following information:
                - {fields_list}
                
                If any required information is missing, note it for follow-up.
                If all information is collected, mark this step as complete.
                """
        else:
            return """**Observe: Track Result**

            Analyze the result of the last action:
            - Was it successful?
            - What information did we gain?
            - What should we do next?
            """

    def _create_update_state_function(self, required_fields: List[str]) -> Dict[str, Any]:
        """Create function for updating observation state."""
        properties = {}

        for field in required_fields:
            properties[field] = {
                "type": "string",
                "description": f"The {field} mentioned by the user"
            }

        function_config = {
            "name": "update_state",
            "description": "Update conversation state with extracted information",
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": []  # All optional, extract what's available
            }
        }

        return function_config

    def _filter_functions_for_action(
        self,
        functions: List[Dict[str, Any]],
        action_type: str
    ) -> List[Dict[str, Any]]:
        """
        Filter functions based on action type to prevent unwanted function calling.

        CRITICAL: Conversational nodes (goal_collection, general) should have NO functions
        so the LLM produces text responses that go to TTS pipeline instead of calling functions.

        Action nodes (search, handover, end) keep ONLY their specific function.

        Args:
            functions: Original list of functions from node
            action_type: Type of action (goal_collection, search, handover, end, general)

        Returns:
            Filtered list of functions (empty for conversational nodes)
        """
        # Conversational nodes: NO functions (enables speech output to TTS)
        if action_type in ["goal_collection", "general"]:
            return []

        # Action nodes: Keep ONLY the specific action function
        filtered = []
        for func in functions:
            # Handle both dict and object
            if isinstance(func, dict):
                func_name = func.get("name", "")
            else:
                func_name = getattr(func, "name", "")

            # Filter based on action type
            if action_type == "search" and func_name == "search_docs":
                filtered.append(func)
            elif action_type == "handover" and func_name == "handover":
                filtered.append(func)
            elif action_type == "end" and func_name == "end_call":
                filtered.append(func)

        return filtered

    def _create_decide_action_function(
        self,
        available_actions: List[str],
        next_action: str
    ) -> Dict[str, Any]:
        """
        Create function for Think node to decide next action.

        This function:
        - Presents available actions as enum
        - LLM selects one via function call
        - Prevents action name from being spoken (silent transition)

        Args:
            available_actions: List of available action names
            next_action: Default next action if none chosen

        Returns:
            Function config dict
        """
        function_config = {
            "name": "decide_next_action",
            "description": "Choose the next action based on conversation context and goals",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": available_actions,
                        "description": "The next action to take"
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


class ReActFlowConverter:
    """
    Converts standard flow nodes to ReAct-optimized flow.

    Takes output from flow_generator_v3 and transforms it into
    Think → Act → Observe loop structure.
    """

    def __init__(
        self,
        instructions: str,
        identity: str,
        objections: Dict[str, str]
    ):
        """
        Initialize converter.

        Args:
            instructions: Combined instructions
            identity: Agent identity
            objections: Objection handling map
        """
        self.builder = ReActNodeBuilder(instructions, identity, objections)
        self.instructions = instructions
        self.identity = identity
        self.objections = objections

    def convert(self, standard_nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert standard nodes to ReAct flow.

        SIMPLIFIED STRUCTURE (No Think nodes - they caused LLM to speak action names):
        - For each standard node: Act → Observe pair
        - Observe nodes handle state tracking and transitions
        - No explicit "thinking" turns (happens internally)

        Args:
            standard_nodes: Output from flow_generator_v3

        Returns:
            ReAct-optimized node list (Act + Observe pairs only)
        """
        react_nodes = []

        # Convert each node to Act + Observe pair
        for idx, node in enumerate(standard_nodes):
            # Determine action type
            action_type = self._determine_action_type(node)

            # Build Act node (focused conversation turn)
            act_node = self.builder.build_act_node(node, action_type)
            react_nodes.append(act_node)

            # Build Observe node (state tracking - silent)
            next_node_idx = idx + 1
            next_node = None
            if next_node_idx < len(standard_nodes):
                # Get next node name
                next_std_node = standard_nodes[next_node_idx]
                if isinstance(next_std_node, dict):
                    next_node = f"act_{next_std_node.get('name', f'action_{next_node_idx}')}"
                else:
                    next_node = f"act_{getattr(next_std_node, 'name', f'action_{next_node_idx}')}"

            required_fields = self._extract_required_fields(node)

            # Get current node name
            if isinstance(node, dict):
                node_name = node.get("name", f"action_{idx}")
            else:
                node_name = getattr(node, "name", f"action_{idx}")

            observe_node = self.builder.build_observe_node(
                action_name=node_name,
                next_node=next_node or "end",
                required_fields=required_fields
            )
            react_nodes.append(observe_node)

        return react_nodes

    def _determine_action_type(self, node: Dict[str, Any]) -> str:
        """
        Determine what type of action this node represents.

        IMPORTANT: Check node NAME first (most reliable), then functions.
        This prevents misclassification when nodes have multiple functions.
        """
        # Handle both dict and NodeConfig objects
        if isinstance(node, dict):
            name = node.get("name", "").lower()
            functions = node.get("functions", [])
        else:
            # NodeConfig object
            name = getattr(node, "name", "").lower()
            functions = getattr(node, "functions", [])

        # PRIORITY 1: Check node name patterns (most reliable)
        # Check for specific action nodes first
        if name == "end" or "end_conversation" in name or "goodbye" in name:
            return "end"

        if "qa_router" in name or "search" in name or "faq" in name or "knowledge" in name:
            return "search"

        if "handover" in name or "transfer" in name or "human" in name or "escalate" in name:
            return "handover"

        # Check for goal/question nodes
        if any(keyword in name for keyword in ["goal", "collect", "ask", "question", "always_ask", "main_goal", "required"]):
            return "goal_collection"

        # PRIORITY 2: Check function names (only if name doesn't match)
        # Extract all function names
        func_names = []
        for func in functions:
            if isinstance(func, dict):
                func_names.append(func.get("name", ""))
            else:
                func_names.append(getattr(func, "name", ""))

        # Count specific function types to determine primary purpose
        has_search = any("search" in fn for fn in func_names)
        has_handover = any("handover" in fn for fn in func_names)
        has_end = any("end_call" in fn for fn in func_names)
        has_collect = any("collect" in fn for fn in func_names)

        # If node has ONLY one type of function, use that
        if has_search and not has_handover and not has_end and not has_collect:
            return "search"
        if has_handover and not has_search and not has_end and not has_collect:
            return "handover"
        if has_end and not has_search and not has_handover and not has_collect:
            return "end"
        if has_collect and not has_search and not has_handover and not has_end:
            return "goal_collection"

        # Default: goal_collection (safest - will speak, not call functions)
        return "goal_collection"

    def _extract_required_fields(self, node: Dict[str, Any]) -> List[str]:
        """Extract required fields from node metadata or functions."""
        # Handle both dict and NodeConfig objects
        if isinstance(node, dict):
            metadata = node.get("metadata", {})
            functions = node.get("functions", [])
        else:
            metadata = getattr(node, "metadata", {})
            functions = getattr(node, "functions", [])

        # Check metadata first
        if isinstance(metadata, dict) and "required_fields" in metadata:
            return metadata["required_fields"]

        # Extract from function parameters
        required_fields = []

        for func in functions:
            # Handle both dict and FlowsFunctionSchema objects
            if isinstance(func, dict):
                params = func.get("parameters", {})
            else:
                params = getattr(func, "parameters", {})

            if isinstance(params, dict):
                properties = params.get("properties", {})
                if isinstance(properties, dict):
                    required_fields.extend(properties.keys())

        return required_fields


# Integration helper

def create_react_flow(
    standard_nodes: List[Dict[str, Any]],
    instructions: str,
    identity: str,
    objections: Dict[str, str]
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Create ReAct-optimized flow from standard nodes.

    Args:
        standard_nodes: Output from flow_generator_v3.create_smart_flow()
        instructions: Combined instructions text
        identity: Agent identity
        objections: Objection handling dict

    Returns:
        Tuple of (react_nodes, react_config)
    """
    converter = ReActFlowConverter(instructions, identity, objections)
    react_nodes = converter.convert(standard_nodes)

    react_config = {
        "flow_type": "react",
        "instructions": instructions,
        "identity": identity,
        "objections": objections,
        "num_standard_nodes": len(standard_nodes),
        "num_react_nodes": len(react_nodes)
    }

    return react_nodes, react_config
