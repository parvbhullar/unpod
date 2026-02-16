"""
Flow State Manager for Section-Based Flows

Provides type-safe wrapper around FlowManager.state for managing
conversation state across node transitions.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from pipecat_flows import FlowManager


class FlowStateManager:
    """
    Type-safe wrapper around flow_manager.state.

    Manages:
    - Collected data from user responses
    - Condition evaluation results
    - Objection handling history
    - Conversation path tracking
    - Section transitions
    """

    def __init__(self, flow_manager: FlowManager):
        self.fm = flow_manager

        # Initialize state structure if not already done
        if not self.fm.state.get('initialized'):
            self._initialize_state()

    def _initialize_state(self):
        """Initialize state structure on first use."""
        self.fm.state.update({
            'initialized': True,
            'collected_data': {},        # User responses: {field_name: value}
            'conditions_met': {},          # Condition results: {condition_id: bool}
            'objections_handled': [],      # List of handled objections
            'current_section_id': None,    # Current section being processed
            'previous_section_id': None,   # Previous section (for back navigation)
            'conversation_path': [],       # Breadcrumb trail of section IDs
            'metadata': {},                # Additional metadata
            'timestamp_start': datetime.now().isoformat(),
            'timestamp_last_update': datetime.now().isoformat()
        })

    # Data Management

    def store_field(self, field_name: str, value: Any):
        """Store collected data from user response."""
        self.fm.state['collected_data'][field_name] = value
        self._update_timestamp()

    def get_field(self, field_name: str, default: Any = None) -> Any:
        """Retrieve collected data."""
        return self.fm.state['collected_data'].get(field_name, default)

    def has_field(self, field_name: str) -> bool:
        """Check if field has been collected."""
        return field_name in self.fm.state['collected_data']

    def get_all_collected_data(self) -> Dict[str, Any]:
        """Get all collected data."""
        return dict(self.fm.state['collected_data'])

    # Condition Management

    def set_condition_result(self, condition_id: str, result: bool):
        """Store condition evaluation result."""
        self.fm.state['conditions_met'][condition_id] = result
        self._update_timestamp()

    def get_condition_result(self, condition_id: str) -> Optional[bool]:
        """Get condition evaluation result."""
        return self.fm.state['conditions_met'].get(condition_id)

    def was_condition_met(self, condition_id: str) -> bool:
        """Check if condition was evaluated as true."""
        return self.fm.state['conditions_met'].get(condition_id, False)

    # Objection Management

    def record_objection(self, objection_type: str, details: Optional[str] = None):
        """Record that an objection was handled."""
        objection_record = {
            'type': objection_type,
            'timestamp': datetime.now().isoformat(),
            'details': details,
            'section_id': self.fm.state.get('current_section_id')
        }
        self.fm.state['objections_handled'].append(objection_record)
        self._update_timestamp()

    def get_objections(self) -> List[Dict[str, Any]]:
        """Get all handled objections."""
        return list(self.fm.state['objections_handled'])

    def has_handled_objection(self, objection_type: str) -> bool:
        """Check if specific objection type was already handled."""
        return any(
            obj['type'] == objection_type
            for obj in self.fm.state['objections_handled']
        )

    # Section Navigation

    def transition_to(self, section_id: str):
        """Record transition to new section."""
        self.fm.state['previous_section_id'] = self.fm.state.get('current_section_id')
        self.fm.state['current_section_id'] = section_id
        self.fm.state['conversation_path'].append(section_id)
        self._update_timestamp()

    def get_current_section(self) -> Optional[str]:
        """Get current section ID."""
        return self.fm.state.get('current_section_id')

    def get_previous_section(self) -> Optional[str]:
        """Get previous section ID."""
        return self.fm.state.get('previous_section_id')

    def get_conversation_path(self) -> List[str]:
        """Get breadcrumb trail of all sections visited."""
        return list(self.fm.state.get('conversation_path', []))

    def can_return_to_previous(self) -> bool:
        """Check if we can navigate back to previous section."""
        return self.fm.state.get('previous_section_id') is not None

    # Metadata

    def set_metadata(self, key: str, value: Any):
        """Store metadata."""
        self.fm.state['metadata'][key] = value
        self._update_timestamp()

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata."""
        return self.fm.state['metadata'].get(key, default)

    # Utilities

    def _update_timestamp(self):
        """Update last modification timestamp."""
        self.fm.state['timestamp_last_update'] = datetime.now().isoformat()

    def get_state_summary(self) -> Dict[str, Any]:
        """Get summary of current state for debugging."""
        return {
            'current_section': self.get_current_section(),
            'previous_section': self.get_previous_section(),
            'collected_fields': list(self.fm.state['collected_data'].keys()),
            'conditions_evaluated': len(self.fm.state['conditions_met']),
            'objections_handled': len(self.fm.state['objections_handled']),
            'path_length': len(self.get_conversation_path()),
            'duration': self._calculate_duration()
        }

    def _calculate_duration(self) -> Optional[str]:
        """Calculate conversation duration."""
        try:
            start = datetime.fromisoformat(self.fm.state['timestamp_start'])
            last = datetime.fromisoformat(self.fm.state['timestamp_last_update'])
            duration = last - start
            return str(duration)
        except:
            return None

    def clear(self):
        """Clear all state (for testing)."""
        self.fm.state.clear()
        self._initialize_state()
