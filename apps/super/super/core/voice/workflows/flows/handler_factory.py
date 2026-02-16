"""
Handler Factory for Section-Based Flows

Generates specialized handler functions for each section type.
Each handler manages data collection, validation, state updates, and transitions.
"""

from typing import Callable
from pipecat_flows import FlowArgs, FlowManager, FlowResult
from .section_parser import ParsedSection, ParsedFlowConfig
from .state_manager import FlowStateManager
from .transition_manager import TransitionManager


class HandlerFactory:
    """
    Factory for creating specialized handler functions per section type.

    Handler Types:
    - question_handler: Collect data, validate, store in state
    - condition_handler: Evaluate if/yes/no, branch accordingly
    - objection_handler: Handle interruption, return to flow
    - greeting_handler: Initial interaction
    - pitch_handler: Present value proposition
    """

    def __init__(self, flow_config: ParsedFlowConfig):
        self.config = flow_config
        self.handlers = {}  # Cache of generated handlers

    def create_handler_for_section(self, section: ParsedSection) -> Callable:
        """
        Create appropriate handler function based on section type.

        Args:
            section: ParsedSection to create handler for

        Returns:
            Async handler function with signature:
            async (args: FlowArgs, flow_manager: FlowManager) -> tuple[FlowResult, NodeConfig]
        """
        # Check cache
        if section.id in self.handlers:
            return self.handlers[section.id]

        # Create handler based on type
        if section.type == 'greeting':
            handler = self._create_greeting_handler(section)
        elif section.type == 'question':
            handler = self._create_question_handler(section)
        elif section.type == 'pitch':
            handler = self._create_pitch_handler(section)
        elif section.type == 'condition':
            handler = self._create_condition_handler(section)
        elif section.type == 'objection':
            handler = self._create_objection_handler(section)
        else:
            # Default generic handler
            handler = self._create_generic_handler(section)

        # Cache and return
        self.handlers[section.id] = handler
        return handler

    def _create_greeting_handler(self, section: ParsedSection) -> Callable:
        """Create handler for greeting section."""

        async def greeting_handler(args: FlowArgs, flow_manager: FlowManager):
            """Auto-generated handler for greeting section."""
            # Initialize state manager
            state_mgr = FlowStateManager(flow_manager)

            # Store any collected fields (e.g., name from greeting)
            for field in section.required:
                if field in args:
                    state_mgr.store_field(field, args[field])

            # Record transition
            state_mgr.transition_to(section.id)

            # Determine next section
            transition_mgr = TransitionManager(self.config, state_mgr)
            next_section = transition_mgr.get_next_section(section, args)

            # Create result
            result_data = {field: args.get(field) for field in section.required if field in args}
            result = self._create_flow_result(section, result_data)

            # Import node factory (avoid circular import)
            from .node_factory import NodeFactory
            node_factory = NodeFactory(self.config, self)

            # Get next node
            if next_section:
                next_node = node_factory.create_node_for_section(next_section)
            else:
                # End of flow - go to free conversation
                from super.core.voice.workflows.flows.flow_generator import start_convo
                next_node = start_convo()

            return result, next_node

        return greeting_handler

    def _create_question_handler(self, section: ParsedSection) -> Callable:
        """Create handler for question/data collection section."""

        async def question_handler(args: FlowArgs, flow_manager: FlowManager):
            """Auto-generated handler for question section."""
            # Initialize managers
            state_mgr = FlowStateManager(flow_manager)

            # Validate required fields
            missing = [f for f in section.required if not args.get(f)]
            if missing:
                # Stay on current node if data missing
                from .node_factory import NodeFactory
                node_factory = NodeFactory(self.config, self)
                current_node = node_factory.create_node_for_section(section)
                return None, current_node

            # Store collected data
            for field in section.required:
                state_mgr.store_field(field, args[field])

            # Record transition
            state_mgr.transition_to(section.id)

            # Determine next section
            transition_mgr = TransitionManager(self.config, state_mgr)
            next_section = transition_mgr.get_next_section(section, args)

            # Create result
            result_data = {field: args[field] for field in section.required}
            result = self._create_flow_result(section, result_data)

            # Get next node
            from .node_factory import NodeFactory
            node_factory = NodeFactory(self.config, self)

            if next_section:
                next_node = node_factory.create_node_for_section(next_section)
            else:
                # End of flow
                from super.core.voice.workflows.flows.flow_generator import start_convo
                next_node = start_convo()

            return result, next_node

        return question_handler

    def _create_pitch_handler(self, section: ParsedSection) -> Callable:
        """Create handler for pitch/value proposition section."""

        async def pitch_handler(args: FlowArgs, flow_manager: FlowManager):
            """Auto-generated handler for pitch section."""
            # Similar to question handler but for pitch content
            state_mgr = FlowStateManager(flow_manager)

            # Store any responses (e.g., interest level)
            for field in section.required:
                if field in args:
                    state_mgr.store_field(field, args[field])

            # Record transition
            state_mgr.transition_to(section.id)

            # Determine next section
            transition_mgr = TransitionManager(self.config, state_mgr)
            next_section = transition_mgr.get_next_section(section, args)

            # Create result
            result_data = {field: args.get(field) for field in section.required if field in args}
            result = self._create_flow_result(section, result_data)

            # Get next node
            from .node_factory import NodeFactory
            node_factory = NodeFactory(self.config, self)

            if next_section:
                next_node = node_factory.create_node_for_section(next_section)
            else:
                from super.core.voice.workflows.flows.flow_generator import start_convo
                next_node = start_convo()

            return result, next_node

        return pitch_handler

    def _create_condition_handler(self, section: ParsedSection) -> Callable:
        """
        Create handler for conditional (If YES/NO) section.

        CRITICAL FIX: Don't re-evaluate condition here - read cached result from state.
        Condition was already evaluated in question transition.
        """

        async def condition_handler(args: FlowArgs, flow_manager: FlowManager):
            """Auto-generated handler for condition section."""
            state_mgr = FlowStateManager(flow_manager)

            from .node_factory import NodeFactory
            node_factory = NodeFactory(self.config, self)

            # Read cached condition result (already evaluated in question transition)
            condition_result = state_mgr.get_condition_result(section.id)

            if condition_result is None:
                # Fallback: condition wasn't evaluated yet (shouldn't happen)
                # This means we're being called directly without going through question transition
                from .transition_manager import TransitionManager
                transition_mgr = TransitionManager(self.config, state_mgr)
                condition_result = transition_mgr.should_activate_condition(section, args)

            # Store any collected data from this conditional section
            for field in section.required:
                if field in args:
                    state_mgr.store_field(field, args[field])

            # Record transition
            state_mgr.transition_to(section.id)

            # Route to appropriate branch based on cached result
            if condition_result:
                # Condition met - go to YES target
                target_id = section.yes_target
            else:
                # Condition not met - go to NO target (or post-condition)
                target_id = section.no_target

            # Get target section
            next_section = None
            if target_id:
                next_section = self.config.sections_by_id.get(target_id)

            # Create result
            result_data = {
                'condition_met': condition_result,
                'condition_type': section.condition_type
            }
            result_data.update({field: args.get(field) for field in section.required if field in args})
            result = self._create_flow_result(section, result_data)

            # Get next node
            if next_section:
                next_node = node_factory.create_node_for_section(next_section)
            else:
                # No target specified, go to post-condition or end conversation
                from .transition_manager import TransitionManager
                transition_mgr = TransitionManager(self.config, state_mgr)
                post_section = transition_mgr.get_post_condition_section(section)

                if post_section:
                    next_node = node_factory.create_node_for_section(post_section)
                else:
                    from super.core.voice.workflows.flows.flow_generator import start_convo
                    next_node = start_convo()

            return result, next_node

        return condition_handler

    def _create_objection_handler(self, section: ParsedSection) -> Callable:
        """Create handler for objection section."""

        async def objection_handler(args: FlowArgs, flow_manager: FlowManager):
            """Auto-generated handler for objection section."""
            state_mgr = FlowStateManager(flow_manager)

            # Record objection
            objection_type = section.trigger_keywords[0] if section.trigger_keywords else section.section_name
            details = args.get('details', None)
            state_mgr.record_objection(objection_type, details)

            # Store any additional data collected during objection handling
            for field in section.required:
                if field in args:
                    state_mgr.store_field(field, args[field])

            # Record transition
            state_mgr.transition_to(section.id)

            # Return to previous section or continue flow
            transition_mgr = TransitionManager(self.config, state_mgr)
            next_section = transition_mgr.get_next_section(section, args)

            # Create result
            result_data = {
                'objection_type': objection_type,
                'handled': True
            }
            result_data.update({field: args.get(field) for field in section.required if field in args})
            result = self._create_flow_result(section, result_data)

            # Get next node
            from .node_factory import NodeFactory
            node_factory = NodeFactory(self.config, self)

            if next_section:
                next_node = node_factory.create_node_for_section(next_section)
            else:
                from super.core.voice.workflows.flows.flow_generator import start_convo
                next_node = start_convo()

            return result, next_node

        return objection_handler

    def _create_generic_handler(self, section: ParsedSection) -> Callable:
        """Create generic handler for unrecognized section types."""

        async def generic_handler(args: FlowArgs, flow_manager: FlowManager):
            """Generic handler for section."""
            state_mgr = FlowStateManager(flow_manager)

            # Store any collected data
            for field in section.required:
                if field in args:
                    state_mgr.store_field(field, args[field])

            # Record transition
            state_mgr.transition_to(section.id)

            # Get next section
            transition_mgr = TransitionManager(self.config, state_mgr)
            next_section = transition_mgr.get_next_section(section, args)

            # Create result
            result_data = {field: args.get(field) for field in section.required if field in args}
            result = self._create_flow_result(section, result_data)

            # Get next node
            from .node_factory import NodeFactory
            node_factory = NodeFactory(self.config, self)

            if next_section:
                next_node = node_factory.create_node_for_section(next_section)
            else:
                from super.core.voice.workflows.flows.flow_generator import start_convo
                next_node = start_convo()

            return result, next_node

        return generic_handler

    def _create_flow_result(self, section: ParsedSection, data: dict) -> FlowResult:
        """
        Create FlowResult dynamically for section.

        Args:
            section: Section metadata
            data: Data to include in result

        Returns:
            FlowResult instance
        """
        result_class_name = f"{section.id.title().replace('_', '')}Result"

        attributes = {}
        coerced_data = {}
        for field, value in data.items():
            field_type = section.field_types.get(field, 'string')

            if field_type == 'boolean' and isinstance(value, bool):
                attributes[field] = bool
                coerced_data[field] = value
            elif field_type == 'number':
                attributes[field] = float
                try:
                    coerced_data[field] = float(value)
                except (TypeError, ValueError):
                    coerced_data[field] = value
            else:
                attributes[field] = str
                coerced_data[field] = value

        if not attributes:
            attributes = {'ack': bool}
            coerced_data = {'ack': True}

        result_class = type(
            result_class_name,
            (FlowResult,),
            attributes
        )

        return result_class(**coerced_data)

    def create_all_handlers(self) -> dict:
        """
        Create handlers for all sections in flow config.

        Returns:
            Dict mapping section_id to handler function
        """
        handlers = {}

        # Create handlers for all section types
        all_sections = []

        if self.config.greeting:
            all_sections.append(self.config.greeting)

        all_sections.extend(self.config.questions)
        all_sections.extend(self.config.pitches)
        all_sections.extend(self.config.conditions)
        all_sections.extend(self.config.objections)

        for section in all_sections:
            handlers[section.id] = self.create_handler_for_section(section)

        return handlers
