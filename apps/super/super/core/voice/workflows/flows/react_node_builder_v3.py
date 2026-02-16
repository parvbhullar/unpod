"""
ReAct Node Builder V3 - Central Node → Think Function → Act Architecture

This module implements a ReAct pattern following the flow:
Central Node → Think Function → Act

**CENTRAL NODE** (Main Conversational Hub):
- Has FULL context (instructions + identity + objections + state)
- Handles user communication (can speak via TTS)
- Has ALL available functions registered
- Uses a special "think" function to reason about next action
- The "think" function returns which Act node to route to

**THINK FUNCTION** (Reasoning Function):
- A function available in the Central Node
- Called by LLM when it needs to decide next action
- Analyzes conversation state and user intent
- Returns the name of the Act node to execute
- Silent operation (no TTS output)

**ACT NODES** (Execution Specialists):
- Each action has its own dedicated Act node
- Executes ONE specific function
- Focused context for that specific action
- Returns control to Central Node after execution
- Can output user feedback (TTS) when appropriate

**Flow Pattern**:
1. User speaks → Central Node (handles conversation)
2. Central Node calls → Think Function (decides next action)
3. Think Function returns → Act node name
4. System routes to → Act Node (executes action)
5. Act Node completes → Returns to Central Node
6. Loop continues...

**Example Turn**:
User: "What courses do you offer?"
1. Central Node: Receives input, has conversation context
2. Central Node calls: think_function() → analyzes → returns "act_search_docs"
3. System routes to: act_search_docs node
4. act_search_docs: Outputs "Let me check..." → calls search_docs() → returns results
5. Returns to: Central Node with results
6. Central Node: Presents results to user

**Key Improvements over V2**:
- Central Node as main hub (not silent Think node)
- Think is a FUNCTION, not a node
- Clearer flow: Central → Think Function → Act → Central
- Better resource usage: one main node + specialized Act nodes
- Maintains conversational continuity in Central Node
"""

from typing import Any, Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
import re

try:
    from pipecat_flows import (
        NodeConfig,
        FlowsFunctionSchema,
        FlowArgs,
        FlowManager,
        FlowResult,
    )
except ImportError:
    # Fallback types for development
    NodeConfig = dict
    FlowsFunctionSchema = dict
    FlowArgs = dict
    FlowManager = object
    FlowResult = object


# ============================================================================
# SECTION 1: FUNCTION REGISTRY (Reuse from V2)
# ============================================================================

@dataclass
class FunctionRegistry:
    """
    Central registry of ALL available functions.

    V3 Enhancement: Each function gets metadata for Act node generation.
    """
    search_docs: Optional[FlowsFunctionSchema] = None
    handover: Optional[FlowsFunctionSchema] = None
    end_call: Optional[FlowsFunctionSchema] = None
    goal_functions: Dict[str, FlowsFunctionSchema] = field(default_factory=dict)

    # V3: Function metadata for Act node customization
    function_metadata: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def get_all_functions(self) -> List[FlowsFunctionSchema]:
        """Get ALL functions for registry."""
        functions = []

        if self.search_docs:
            functions.append(self.search_docs)
        if self.handover:
            functions.append(self.handover)
        if self.end_call:
            functions.append(self.end_call)

        functions.extend(self.goal_functions.values())

        return functions

    def get_function(self, function_name: str) -> Optional[FlowsFunctionSchema]:
        """Get specific function by name."""
        if function_name == "search_docs":
            return self.search_docs
        if function_name == "handover":
            return self.handover
        if function_name == "end_call":
            return self.end_call

        return self.goal_functions.get(function_name)

    def add_goal_function(self, function_config: FlowsFunctionSchema, metadata: Optional[Dict[str, Any]] = None):
        """
        Add a goal collection function with metadata.

        Args:
            function_config: FlowsFunctionSchema object
            metadata: Optional metadata for Act node customization
        """
        if isinstance(function_config, dict):
            func_name = function_config.get("name", "")
        else:
            func_name = getattr(function_config, "name", "")

        if func_name:
            self.goal_functions[func_name] = function_config
            if metadata:
                self.function_metadata[func_name] = metadata

    def get_function_metadata(self, function_name: str) -> Dict[str, Any]:
        """Get metadata for a function (for Act node customization)."""
        return self.function_metadata.get(function_name, {})

    def get_all_function_names(self) -> List[str]:
        """Get list of all available function names."""
        names = []
        if self.search_docs:
            names.append("search_docs")
        if self.handover:
            names.append("handover")
        if self.end_call:
            names.append("end_call")
        names.extend(self.goal_functions.keys())
        return names


# ============================================================================
# SECTION 2: OBSERVATION STATE (Enhanced for V3)
# ============================================================================

@dataclass
class ObservationState:
    """
    Enhanced observation state for V3 with DSPy-ready context.
    """
    # Action history
    actions_taken: List[Dict[str, Any]] = field(default_factory=list)
    last_action: Optional[str] = None
    last_action_result: Any = None

    # Goal tracking
    current_goal_id: Optional[str] = None
    collected_fields: Dict[str, Any] = field(default_factory=dict)
    missing_fields: List[str] = field(default_factory=list)
    goals_completed: List[str] = field(default_factory=list)
    goals_pending: List[str] = field(default_factory=list)

    # Conversation state
    turn_count: int = 0
    last_user_message: str = ""
    last_bot_response: str = ""

    # Objection handling
    active_objection: Optional[str] = None
    objection_handled: bool = False

    def add_action(self, action_name: str, result: Any, success: bool = True):
        """Record an action taken."""
        self.actions_taken.append({
            "action": action_name,
            "result": result,
            "success": success,
            "turn": self.turn_count
        })
        self.last_action = action_name
        self.last_action_result = result

    def update_goal_progress(self, goal_id: str, fields: Dict[str, Any]):
        """Update collected fields for current goal."""
        self.current_goal_id = goal_id
        self.collected_fields.update(fields)

    def complete_goal(self, goal_id: str):
        """Mark goal as completed."""
        if goal_id in self.goals_pending:
            self.goals_pending.remove(goal_id)
        if goal_id not in self.goals_completed:
            self.goals_completed.append(goal_id)

    def to_context_summary(self) -> str:
        """Generate compact summary for Think node context."""
        parts = []

        if self.last_action:
            parts.append(f"Last Action: {self.last_action}")

        if self.collected_fields:
            fields_str = ", ".join(f"{k}={v}" for k, v in self.collected_fields.items())
            parts.append(f"Collected: {fields_str}")

        if self.missing_fields:
            parts.append(f"Missing: {', '.join(self.missing_fields)}")

        if self.goals_completed:
            parts.append(f"Completed: {len(self.goals_completed)} goals")

        if self.goals_pending:
            parts.append(f"Pending: {len(self.goals_pending)} goals")

        if self.active_objection:
            parts.append(f"Active Objection: {self.active_objection}")

        return " | ".join(parts) if parts else "Conversation started"


# ============================================================================
# SECTION 3: CENTRAL NODE BUILDER (Main Conversational Hub with Think Function)
# ============================================================================

class CentralNodeBuilder:
    """
    Builder for Central Node - the main conversational hub of V3 architecture.

    Central Node responsibilities:
    - Handle user communication (can speak via TTS)
    - Has FULL context (instructions + identity + objections + state)
    - Has ALL available functions registered (including Think function)
    - Think function decides which Act node to route to
    - Maintains conversational flow
    """

    def __init__(
        self,
        instructions: str,
        identity: str,
        objections: Dict[str, str],
        function_registry: FunctionRegistry,
        observation_state: Optional[ObservationState] = None
    ):
        self.instructions = instructions
        self.identity = identity
        self.objections = objections
        self.function_registry = function_registry
        self.observation_state = observation_state or ObservationState()
        self.node_registry = {}  # Store node references for routing

    def build(self, node_id: str = "main") -> Dict[str, Any]:
        """
        Build the Central Node with Think function.

        Returns:
            NodeConfig dict for Central node
        """
        # Build full context for conversation
        role_message = self._build_role_context()

        # Build conversational task
        task_message = self._build_conversational_task()

        # Get ALL functions (including Think function)
        all_functions = self._build_all_functions()

        central_node = {
            "name": f"central_{node_id}",
            "role_messages": [{"role": "system", "content": role_message}],
            "task_messages": [{"role": "system", "content": task_message}],
            "functions": all_functions,  # ALL functions including think()
            "pre_actions": [],
            "post_actions": [],
            "respond_immediately": True,  # CAN output to TTS
            "metadata": {
                "node_type": "central",
                "is_central_node": True,
                "has_full_context": True,
                "can_speak": True,
                "has_think_function": True
            }
        }

        return central_node

    def _build_role_context(self) -> str:
        """Build FULL context for Central node."""
        parts = []

        # Instructions
        if self.instructions:
            parts.append(f"## Core Instructions\n{self.instructions}")

        # Identity
        if self.identity:
            parts.append(f"## Agent Identity\n{self.identity}")

        # Objections
        if self.objections:
            obj_text = "\n\n".join(
                f"**{obj_id}**: {content}"
                for obj_id, content in self.objections.items()
            )
            parts.append(f"## Objection Handling\n{obj_text}")

        # Current state
        state_summary = self.observation_state.to_context_summary()
        parts.append(f"## Current State\n{state_summary}")

        return "\n\n".join(parts)

    def _build_conversational_task(self) -> str:
        """Build conversational task for Central node."""
        task = """**Central Conversational Hub**
        
        You are the main conversational agent. Handle the conversation naturally while using functions appropriately.
        
        **Your Capabilities**:
        1. Engage in natural conversation with users
        2. Use the "think" function when you need to reason about next steps
        3. Use action functions (search_docs, collect_*, handover, end_call) for specific tasks
        4. Maintain context and conversation flow
        
        **When to Use Think Function**:
        - When you need to decide what action to take next
        - When the conversation flow requires complex reasoning
        - Call think() to analyze the situation and get guidance
        
        **When to Use Action Functions Directly**:
        - For simple, straightforward actions (collecting name, phone, etc.)
        - For immediate responses (search_docs when user asks a question)
        - For ending or transferring the call
        
        **Guidelines**:
        1. Be conversational and natural - you CAN speak to users
        2. Use functions when needed, but don't announce every function call
        3. For complex decisions, use the think() function first
        4. Maintain your persona and follow instructions at all times
        
        **Example Flow**:
        User: "What courses do you offer?"
        You: "Let me check that for you..." *calls search_docs("courses")* "We offer UPSC Foundation, Mains Guidance..."
        
        User: "Can I know the fee?"
        You: *calls think() to decide if we have fee info or need to search* → *routes to appropriate action*
        """
        return task

    def _build_all_functions(self) -> List[FlowsFunctionSchema]:
        """Get ALL functions including Think function."""
        functions = []

        # 1. Add Think function (special reasoning function)
        think_function = self._create_think_function()
        functions.append(think_function)

        # 2. Add all registered functions from registry
        functions.extend(self.function_registry.get_all_functions())

        return functions

    def _create_think_function(self) -> FlowsFunctionSchema:
        """
        Create Think function for Central node.

        This function is CALLED by the LLM when it needs to reason about what to do next.
        It returns which Act node to route to.
        """
        available_actions = self.function_registry.get_all_function_names()

        # Capture references for closure
        observation_state = self.observation_state
        node_registry = self.node_registry
        function_registry = self.function_registry

        def suggest_action_static(situation: str, reasoning: str) -> str:
            """Static version of _suggest_action for use in handler."""
            situation_lower = situation.lower()
            reasoning_lower = reasoning.lower()

            # Check for search/question keywords
            if any(word in situation_lower for word in ["what", "how", "when", "where", "course", "fee", "program"]):
                return "search_docs"

            # Check for collection keywords
            if any(word in situation_lower for word in ["name", "phone", "email", "contact", "collect"]):
                for func_name in function_registry.get_all_function_names():
                    if "collect" in func_name:
                        return func_name

            # Check for end/handover
            if any(word in situation_lower for word in ["end", "goodbye", "bye", "finish"]):
                return "end_call"

            if any(word in situation_lower for word in ["transfer", "human", "agent", "help"]):
                return "handover"

            # Default: continue conversation in central node
            return "continue_conversation"

        async def think_handler(args: FlowArgs, flow_manager: FlowManager):
            """Handle think function call from Central node."""
            situation = args.get("situation", "")
            reasoning = args.get("reasoning", "")

            # Update observation state
            observation_state.turn_count += 1
            observation_state.add_action(
                action_name="think",
                result=f"Situation: {situation} | Reasoning: {reasoning}",
                success=True
            )

            # Determine next action based on reasoning
            suggested_action = suggest_action_static(situation, reasoning)

            # ✅ FIX: Route to appropriate node instead of returning None
            if suggested_action == "continue_conversation":
                # Stay in central node for continued conversation
                next_node_name = "central_main"
            elif suggested_action in function_registry.get_all_function_names():
                # Route to specific Act node
                next_node_name = f"act_{suggested_action}"
            else:
                # Default: stay in central node
                next_node_name = "central_main"

            # Look up node from registry
            next_node = node_registry.get(next_node_name)

            # If node not found in registry, stay in central node
            if not next_node:
                next_node = node_registry.get("central_main")

            result_cls = type("ThinkResult", (FlowResult,), {
                "situation": str,
                "reasoning": str,
                "suggested_action": str
            })

            return result_cls(
                situation=situation,
                reasoning=reasoning,
                suggested_action=suggested_action
            ), next_node  # ✅ Return actual node, not None!

        return FlowsFunctionSchema(
            name="think",
            handler=think_handler,
            description="Analyze the situation and decide the best next action",
            properties={
                "situation": {
                    "type": "string",
                    "description": "Current situation or user request to analyze"
                },
                "reasoning": {
                    "type": "string",
                    "description": "Your reasoning about what should happen next"
                }
            },
            required=["situation"]
        )

    def _suggest_action(self, situation: str, reasoning: str) -> str:
        """Simple heuristic to suggest next action based on situation."""
        situation_lower = situation.lower()
        reasoning_lower = reasoning.lower()

        # Check for search/question keywords
        if any(word in situation_lower for word in ["what", "how", "when", "where", "course", "fee", "program"]):
            return "search_docs"

        # Check for collection keywords
        if any(word in situation_lower for word in ["name", "phone", "email", "contact", "collect"]):
            for func_name in self.function_registry.get_all_function_names():
                if "collect" in func_name:
                    return func_name

        # Check for end/handover
        if any(word in situation_lower for word in ["end", "goodbye", "bye", "finish"]):
            return "end_call"

        if any(word in situation_lower for word in ["transfer", "human", "agent", "help"]):
            return "handover"

        # Default: continue conversation in central node
        return "continue_conversation"


# ============================================================================
# SECTION 4: FUNCTION-ACT NODE BUILDER (Execution Specialists)
# ============================================================================

class FunctionActNodeBuilder:
    """
    Builder for Function-Act Nodes - specialized execution nodes.

    Each Function-Act node:
    - Executes ONE specific function
    - Has focused context for that function
    - Can output user feedback (TTS) when appropriate
    - Returns result to Think node
    """

    def __init__(
        self,
        identity: str,
        function_registry: FunctionRegistry,
        observation_state: Optional[ObservationState] = None
    ):
        self.identity = identity
        self.function_registry = function_registry
        self.observation_state = observation_state or ObservationState()

    def build(
        self,
        function_name: str,
        function_type: str = "general",
        next_node: str = "think_main"
    ) -> Dict[str, Any]:
        """
        Build a Function-Act node for a specific function.

        Args:
            function_name: Name of function to execute
            function_type: Type of function (goal_collection, search, action, general)
            next_node: Node to transition to after execution (usually think_main)

        Returns:
            NodeConfig dict for Function-Act node
        """
        # Get function from registry
        function_config = self.function_registry.get_function(function_name)
        if not function_config:
            raise ValueError(f"Function {function_name} not found in registry")

        # Get metadata for customization
        metadata = self.function_registry.get_function_metadata(function_name)

        # Build focused context
        role_message = self._build_act_context(function_name, function_type, metadata)

        # Build execution task
        task_message = self._build_act_task(function_name, function_type, metadata)

        # Determine if this node should output to TTS
        should_speak = function_type in ["goal_collection", "search", "general"]

        act_node = {
            "name": f"act_{function_name}",
            "role_messages": [{"role": "system", "content": role_message}],
            "task_messages": [{"role": "system", "content": task_message}],
            "functions": [function_config],  # ONLY this function
            "pre_actions": [],
            "post_actions": [],
            "respond_immediately": should_speak,  # Speak for conversational nodes
            "metadata": {
                "node_type": "function_act",
                "function_name": function_name,
                "function_type": function_type,
                "next_node": next_node,
                "can_speak": should_speak
            }
        }

        return act_node

    def _build_act_context(
        self,
        function_name: str,
        function_type: str,
        metadata: Dict[str, Any]
    ) -> str:
        """Build focused context for Function-Act node."""
        parts = []

        # Essential identity (first line)
        if self.identity:
            identity_short = self.identity.split('\n')[0]
            parts.append(identity_short)

        # Function-specific context from metadata
        if metadata.get("context"):
            parts.append(f"\n{metadata['context']}")

        # Current state (what's been collected)
        if self.observation_state.collected_fields:
            fields_str = ", ".join(
                f"{k}: {v}"
                for k, v in self.observation_state.collected_fields.items()
            )
            parts.append(f"\n**Already Collected**: {fields_str}")

        return "\n".join(parts) if parts else "Execute the function."

    def _build_act_task(
        self,
        function_name: str,
        function_type: str,
        metadata: Dict[str, Any]
    ) -> str:
        """Build execution task for Function-Act node."""

        # Custom task from metadata
        if metadata.get("task_message"):
            return metadata["task_message"]

        # Generate based on function type
        if function_type == "goal_collection":
            return self._build_goal_collection_task(function_name, metadata)
        elif function_type == "search":
            return self._build_search_task(function_name)
        elif function_type == "action":
            return self._build_action_task(function_name)
        else:
            return f"Execute {function_name} and provide natural response."

    def _build_goal_collection_task(
        self,
        function_name: str,
        metadata: Dict[str, Any]
    ) -> str:
        """Build task for goal collection functions."""
        required_fields = metadata.get("required_fields", [])
        fields_str = ", ".join(required_fields)

        task = f"""**Collect Information Naturally**

            Execute the {function_name} function to collect: {fields_str}
            
            **Guidelines**:
            1. Ask the question naturally and conversationally
            2. Be warm and friendly (maintain your persona)
            3. Listen for the information in the user's response
            4. Call the function with the collected data
            
            **Example Flow**:
            - You: "May I have your name please?"
            - User: "I'm Raj Kumar"
            - You: *calls {function_name}(name="Raj Kumar")*
            
            Keep it natural and conversational."""

        return task

    def _build_search_task(self, function_name: str) -> str:
        """Build task for search/lookup functions."""
        return f"""**Search and Respond**
        
        1. Briefly acknowledge: "Let me check that for you..."
        2. Call {function_name} with the search query
        3. Receive results
        4. Present results naturally to the user
        
        Keep responses concise and helpful."""

    def _build_action_task(self, function_name: str) -> str:
        """Build task for action functions (handover, end_call)."""
        return f"""**Execute Action**
        
        Execute {function_name} and provide appropriate closing.
        
        Be professional and warm in your final message."""


# ============================================================================
# SECTION 5: REACT FLOW CONVERTER V3
# ============================================================================

class ReActFlowConverterV3:
    """
    Converts standard nodes to V3 ReAct flow.

    Creates:
    1. One Central Node (main conversational hub with think function)
    2. Multiple Function-Act Nodes (one per function)
    3. Routing logic between them
    """

    def __init__(
        self,
        instructions: str,
        identity: str,
        objections: Dict[str, str],
        function_registry: FunctionRegistry
    ):
        self.instructions = instructions
        self.identity = identity
        self.objections = objections
        self.function_registry = function_registry
        self.observation_state = ObservationState()

        # Builders
        self.central_builder = CentralNodeBuilder(
            instructions=instructions,
            identity=identity,
            objections=objections,
            function_registry=function_registry,
            observation_state=self.observation_state
        )

        self.act_builder = FunctionActNodeBuilder(
            identity=identity,
            function_registry=function_registry,
            observation_state=self.observation_state
        )

    def convert(self, standard_nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert standard nodes to V3 ReAct flow.

        Output structure:
        - 1 Central Node (with think function)
        - N Function-Act Nodes (one per unique function)

        Args:
            standard_nodes: Output from flow_generator_v3

        Returns:
            List of V3 ReAct nodes
        """
        react_nodes = []

        # 1. Create Central Node (with think function)
        central_node = self.central_builder.build(node_id="main")
        react_nodes.append(central_node)

        # ✅ FIX: Build node registry for routing
        node_registry = {central_node["name"]: central_node}

        # 2. Create Function-Act nodes for each unique function
        seen_functions = set()

        for node in standard_nodes:
            functions = node.get("functions", [])

            for func in functions:
                # Get function name
                if isinstance(func, dict):
                    func_name = func.get("name", "")
                else:
                    func_name = getattr(func, "name", "")

                if not func_name or func_name in seen_functions:
                    continue

                seen_functions.add(func_name)

                # Determine function type
                function_type = self._determine_function_type(node, func_name)

                # Build Function-Act node (returns to central_main)
                act_node = self.act_builder.build(
                    function_name=func_name,
                    function_type=function_type,
                    next_node="central_main"  # Return to Central Node
                )

                react_nodes.append(act_node)
                node_registry[act_node["name"]] = act_node  # ✅ Register node

        # ✅ FIX: Pass node registry to central builder for think function routing
        self.central_builder.node_registry = node_registry

        return react_nodes

    def _determine_function_type(self, node: Dict[str, Any], func_name: str) -> str:
        """Determine function type for Act node customization."""
        node_name = node.get("name", "").lower()

        # Check function name patterns
        if "search" in func_name or "get_docs" in func_name:
            return "search"

        if "handover" in func_name or "transfer" in func_name:
            return "action"

        if "end_call" in func_name or "end" in func_name:
            return "action"

        # Check node name patterns
        if any(keyword in node_name for keyword in ["goal", "collect", "ask", "question"]):
            return "goal_collection"

        return "general"


# ============================================================================
# SECTION 6: INTEGRATION HELPER
# ============================================================================

def create_react_flow_v3(
    standard_nodes: List[Dict[str, Any]],
    instructions: str,
    identity: str,
    objections: Dict[str, str],
    get_docs_handler: Optional[Callable] = None,
    handover_handler: Optional[Callable] = None,
    end_call_handler: Optional[Callable] = None
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Create V3 ReAct flow from standard nodes.

    Architecture: Central Think Node + Function-Act Nodes

    Args:
        standard_nodes: Output from flow_generator_v3.create_smart_flow()
        instructions: Full instructions textit should be like central node - > think function -> act
        identity: Agent identity
        objections: Objection handling dict
        get_docs_handler: Handler for document search
        handover_handler: Handler for agent handover
        end_call_handler: Handler for call termination

    Returns:
        Tuple of (react_nodes, react_config)
    """
    # Build function registry
    function_registry = FunctionRegistry()

    # Register standard action functions
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

    # Extract and register goal functions from standard nodes
    for node in standard_nodes:
        functions = node.get("functions", [])
        for func in functions:
            # Skip action functions (already registered)
            if isinstance(func, dict):
                func_name = func.get("name", "")
            else:
                func_name = getattr(func, "name", "")

            if func_name not in ["search_docs", "handover", "end_call"]:
                # Extract metadata for Act node customization
                metadata = {
                    "task_message": node.get("task_messages", [{}])[0].get("content", ""),
                    "required_fields": getattr(func, "required", []),
                    "context": node.get("role_messages", [{}])[0].get("content", "")
                }
                function_registry.add_goal_function(func, metadata)

    # Create converter
    converter = ReActFlowConverterV3(
        instructions=instructions,
        identity=identity,
        objections=objections,
        function_registry=function_registry
    )

    # Convert to V3 ReAct nodes
    react_nodes = converter.convert(standard_nodes)

    # Build config
    react_config = {
        "flow_type": "react_v3",
        "architecture": "Central Node → Think Function → Act",
        "num_central_nodes": 1,
        "num_act_nodes": len(react_nodes) - 1,
        "total_functions": len(function_registry.get_all_functions()) + 1,  # +1 for think function
        "flow_pattern": "User → Central Node → Think Function → Act Node → Central Node → ...",
        "features": [
            "Central Node as main conversational hub (CAN speak to users)",
            "Think Function for reasoning (called when needed)",
            "Function-Act Nodes for specialized execution",
            "Clear flow: Central → Think Function → Act → Central",
            "Full context in Central Node (instructions + identity + objections)",
            "All functions available in Central Node",
            "Focused context in Act nodes",
            "Better resource usage and debugging"
        ],
        "components": {
            "central_node": {
                "name": "central_main",
                "role": "Main conversational hub",
                "capabilities": ["Speak to users", "Call think function", "Call action functions", "Maintain context"],
                "has_think_function": True
            },
            "think_function": {
                "name": "think",
                "role": "Reasoning function",
                "capabilities": ["Analyze situation", "Suggest next action", "Silent operation"]
            },
            "act_nodes": {
                "count": len(react_nodes) - 1,
                "role": "Specialized execution nodes",
                "return_to": "central_main"
            }
        }
    }

    return react_nodes, react_config