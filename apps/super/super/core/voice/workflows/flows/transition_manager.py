"""
Transition Manager for Section-Based Flows

Manages transitions between sections based on runtime conditions.
Enables dynamic branching (If YES/NO logic) and conditional flow navigation.
"""

from typing import Optional
from pipecat_flows import FlowArgs
from .section_parser import ParsedSection, ParsedFlowConfig
from .state_manager import FlowStateManager


class TransitionManager:
    """
    Determines next section based on current section type and runtime conditions.

    Handles:
    - Linear transitions (question → question)
    - Conditional branching (If YES → section A, If NO → section B)
    - Objection returns (back to previous section)
    - End-of-flow detection
    """

    def __init__(self, flow_config: ParsedFlowConfig, state_manager: FlowStateManager):
        self.config = flow_config
        self.state = state_manager

    def get_next_section(
        self,
        current_section: ParsedSection,
        args: FlowArgs
    ) -> Optional[ParsedSection]:
        """
        Determine next section based on current section type and state.

        Args:
            current_section: Current section being processed
            args: Arguments from function call

        Returns:
            Next ParsedSection to transition to, or None if end of flow
        """

        if current_section.type == 'greeting':
            return self._handle_greeting_transition(current_section)

        elif current_section.type == 'question' or current_section.type == 'pitch':
            return self._handle_question_transition(current_section, args)

        elif current_section.type == 'condition':
            return self._handle_condition_transition(current_section, args)

        elif current_section.type == 'objection':
            return self._handle_objection_transition(current_section)

        else:
            # Default: follow next_section_id
            return self._get_next_in_sequence(current_section)

    def _handle_greeting_transition(self, section: ParsedSection) -> Optional[ParsedSection]:
        """Handle transition from greeting."""
        # Greeting always goes to next section in flow
        return self._get_next_in_sequence(section)

    def _handle_question_transition(
        self,
        section: ParsedSection,
        args: FlowArgs
    ) -> Optional[ParsedSection]:
        """Handle transition from question section."""
        condition_ids = self.config.conditions_by_parent.get(section.id, [])

        if not condition_ids:
            return self._get_next_in_sequence(section)

        for condition_id in condition_ids:
            condition_section = self.config.sections_by_id.get(condition_id)
            if not condition_section:
                continue

            condition_met = self._evaluate_condition(condition_section, args)
            self.state.set_condition_result(condition_id, condition_met)

            if condition_met:
                return condition_section

        post_condition_id = self.config.post_condition_by_parent.get(section.id)
        if post_condition_id:
            return self.config.sections_by_id.get(post_condition_id)

        return self._skip_conditional_branch(section)

    def _handle_condition_transition(
        self,
        section: ParsedSection,
        args: FlowArgs
    ) -> Optional[ParsedSection]:
        """Handle conditional branching."""
        post_condition = self.get_post_condition_section(section)
        if post_condition:
            return post_condition
        return self._get_next_in_sequence(section)

    def _handle_objection_transition(self, section: ParsedSection) -> Optional[ParsedSection]:
        """Handle return from objection."""
        # Return to previous section
        previous_id = self.state.get_previous_section()

        if previous_id:
            return self.config.sections_by_id.get(previous_id)
        else:
            # Fallback: continue flow
            return self._get_next_in_sequence(section)

    def _evaluate_condition(self, section: ParsedSection, args: FlowArgs) -> bool:
        """
        Evaluate condition based on type and collected data.

        Returns:
            True if condition is met, False otherwise
        """

        if section.condition_type == 'yes':
            # Check if user expressed affirmative intent
            return self._interpret_as_yes(args, section)

        elif section.condition_type == 'no':
            # Check if user expressed negative intent
            return self._interpret_as_no(args, section)

        elif section.condition_type == 'custom':
            # Custom condition logic
            return self._evaluate_custom_condition(section, args)

        # Default: condition not met
        return False

    def should_activate_condition(self, section: ParsedSection, args: FlowArgs) -> bool:
        """Determine whether a condition node should execute."""
        result = self._evaluate_condition(section, args)
        self.state.set_condition_result(section.id, result)
        return result

    def get_post_condition_section(self, section: ParsedSection) -> Optional[ParsedSection]:
        """Return the section that follows a condition (both YES/NO paths)."""
        post_id = self.config.post_condition_by_condition.get(section.id)
        if post_id:
            return self.config.sections_by_id.get(post_id)
        return None

    def _interpret_as_yes(self, args: FlowArgs, section: ParsedSection) -> bool:
        """Interpret arguments/state as affirmative."""
        # Check common affirmative indicators
        yes_indicators = [
            'yes', 'yeah', 'yep', 'sure', 'ok', 'okay', 'interested',
            'true', 'want', 'would like', 'agree', 'accept'
        ]

        # Check all argument values
        for key, value in args.items():
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                value_lower = value.lower().strip()
                if any(indicator in value_lower for indicator in yes_indicators):
                    return True

        # Check collected data for related field
        if section.required:
            for field in section.required:
                field_value = self.state.get_field(field)
                if field_value:
                    if isinstance(field_value, bool):
                        return field_value
                    if isinstance(field_value, str):
                        return any(indicator in field_value.lower() for indicator in yes_indicators)

        # Fallback to parent section data
        parent_id = section.parent_section_id
        if parent_id:
            parent_section = self.config.sections_by_id.get(parent_id)
            if parent_section:
                for field in parent_section.required:
                    field_value = self.state.get_field(field)
                    if field_value:
                        if isinstance(field_value, bool):
                            return field_value
                        if isinstance(field_value, str):
                            if any(indicator in field_value.lower() for indicator in yes_indicators):
                                return True

        return False

    def _interpret_as_no(self, args: FlowArgs, section: ParsedSection) -> bool:
        """Interpret arguments/state as negative."""
        no_indicators = [
            'no', 'nope', 'not', 'dont', "don't", 'never', 'nah',
            'false', 'decline', 'refuse', 'reject', 'uninterested'
        ]

        # Check all argument values
        for key, value in args.items():
            if isinstance(value, bool):
                return not value
            if isinstance(value, str):
                value_lower = value.lower().strip()
                if any(indicator in value_lower for indicator in no_indicators):
                    return True

        # Check collected data
        if section.required:
            for field in section.required:
                field_value = self.state.get_field(field)
                if field_value:
                    if isinstance(field_value, bool):
                        return not field_value
                    if isinstance(field_value, str):
                        return any(indicator in field_value.lower() for indicator in no_indicators)

        parent_id = section.parent_section_id
        if parent_id:
            parent_section = self.config.sections_by_id.get(parent_id)
            if parent_section:
                for field in parent_section.required:
                    field_value = self.state.get_field(field)
                    if field_value:
                        if isinstance(field_value, bool):
                            return not field_value
                        if isinstance(field_value, str):
                            if any(indicator in field_value.lower() for indicator in no_indicators):
                                return True

        return False

    def _evaluate_custom_condition(self, section: ParsedSection, args: FlowArgs) -> bool:
        """Evaluate custom condition logic."""
        # Extract condition from section name
        # E.g., "If customer asks about batches"
        section_name_lower = section.section_name.lower()

        # Check if keywords appear in args or state
        keywords = self._extract_keywords_from_condition_name(section_name_lower)

        # Check args
        for key, value in args.items():
            if isinstance(value, str):
                value_lower = value.lower()
                if any(keyword in value_lower for keyword in keywords):
                    return True

        # Check recent collected data
        collected_data = self.state.get_all_collected_data()
        for key, value in collected_data.items():
            if isinstance(value, str):
                value_lower = value.lower()
                if any(keyword in value_lower for keyword in keywords):
                    return True

        return False

    def _extract_keywords_from_condition_name(self, condition_name: str) -> list:
        """Extract keywords from condition name."""
        # "if customer asks about batches" → ["batches", "asks"]
        # Remove common words
        stop_words = ['if', 'customer', 'user', 'says', 'asks', 'about', 'the', 'a', 'an']

        words = condition_name.split()
        keywords = [word for word in words if word not in stop_words and len(word) > 2]

        return keywords

    def _get_next_in_sequence(self, section: ParsedSection) -> Optional[ParsedSection]:
        """Get next section in flow order."""
        if section.next_section_id:
            return self.config.sections_by_id.get(section.next_section_id)
        return None

    def _skip_conditional_branch(self, section: ParsedSection) -> Optional[ParsedSection]:
        """Skip conditional branch and continue flow."""
        # Find next section after this conditional branch
        current_idx = None
        for idx, section_id in enumerate(self.config.flow_order):
            if section_id == section.id:
                current_idx = idx
                break

        if current_idx is not None and current_idx + 1 < len(self.config.flow_order):
            next_id = self.config.flow_order[current_idx + 1]
            return self.config.sections_by_id.get(next_id)

        return None

    def get_section_by_id(self, section_id: str) -> Optional[ParsedSection]:
        """Get section by ID."""
        return self.config.sections_by_id.get(section_id)
