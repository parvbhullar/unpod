"""
Unit tests for PromptManager template replacement functionality.

Tests cover:
- _replace_template_params method
- _build_template_data method
- Template variable replacement in system prompts
- Edge cases and error handling
"""

import logging
import pytest
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from unittest.mock import MagicMock


@dataclass
class MockUserState:
    """Mock UserState for testing."""

    user_name: str = "User"
    contact_number: Optional[str] = None
    model_config: Optional[Dict[str, Any]] = field(default_factory=dict)
    extra_data: Optional[Dict[str, Any]] = field(default_factory=dict)


class MockAgentConfig:
    """Mock AgentConfig for testing."""

    agent_name: str = "TestAgent"


class TestReplaceTemplateParams:
    """Tests for _replace_template_params method."""

    @pytest.fixture
    def prompt_manager(self):
        """Create a PromptManager instance for testing."""
        from super.core.voice.managers.prompt_manager import PromptManager

        config = {
            "system_prompt": "Test prompt",
            "first_message": "Hello",
            "use_conversational_prompts": False,
            "agent_tone": "professional",
            "language": "en",
        }
        user_state = MockUserState(
            user_name="Test User",
            contact_number="+1234567890",
            model_config={"follow_up_enabled": False, "enable_memory": False},
            extra_data={
                "user_data": {
                    "name": "Rahul Kumar",
                    "product": "Home Loan",
                    "last_digit": "4567",
                    "CUSTOMER_CARE_NUMBER": "1860-267-6060",
                }
            },
        )
        return PromptManager(
            config=config,
            agent_config=MockAgentConfig(),
            session_id="test-session-123",
            tool_calling=False,
            logger=logging.getLogger("test"),
            user_state=user_state,
        )

    @pytest.mark.parametrize(
        "template,expected_values",
        [
            (
                "Hello {{name}}, your product is {{product}}",
                {"name": "Rahul Kumar", "product": "Home Loan"},
            ),
            (
                "Loan ending in {{last_digit}}. Call {{CUSTOMER_CARE_NUMBER}}",
                {"last_digit": "4567", "CUSTOMER_CARE_NUMBER": "1860-267-6060"},
            ),
            (
                "{{name}} - {{product}} - {{last_digit}}",
                {"name": "Rahul Kumar", "product": "Home Loan", "last_digit": "4567"},
            ),
        ],
    )
    def test_replace_template_params_basic(
        self, prompt_manager, template: str, expected_values: Dict[str, str]
    ):
        """Test basic template parameter replacement."""
        result = prompt_manager._replace_template_params(template)

        for key, value in expected_values.items():
            assert value in result, f"Expected '{value}' for key '{key}' in result"
        assert "{{" not in result, "Template markers should be removed"

    def test_replace_template_params_no_markers(self, prompt_manager):
        """Test that text without template markers is returned unchanged."""
        text = "This is plain text without any markers"
        result = prompt_manager._replace_template_params(text)
        assert result == text

    def test_replace_template_params_empty_text(self, prompt_manager):
        """Test that empty text returns empty string."""
        result = prompt_manager._replace_template_params("")
        assert result == ""

    def test_replace_template_params_none_text(self, prompt_manager):
        """Test that None text returns None/empty."""
        result = prompt_manager._replace_template_params(None)
        assert result is None or result == ""

    def test_replace_template_params_unknown_variable(self, prompt_manager):
        """Test that unknown template variables are kept as-is."""
        template = "Hello {{unknown_variable}}, your name is {{name}}"
        result = prompt_manager._replace_template_params(template)

        assert "Rahul Kumar" in result
        assert "{{unknown_variable}}" in result

    def test_replace_template_params_duplicate_variables(self, prompt_manager):
        """Test replacement of duplicate template variables."""
        template = "{{name}} said hello. {{name}} is happy."
        result = prompt_manager._replace_template_params(template)

        assert result == "Rahul Kumar said hello. Rahul Kumar is happy."

    def test_replace_template_params_with_additional_data(self, prompt_manager):
        """Test replacement with additional data passed directly."""
        template = "Hello {{custom_field}}"
        result = prompt_manager._replace_template_params(
            template, data={"custom_field": "CustomValue"}
        )

        assert result == "Hello CustomValue"

    def test_replace_template_params_additional_data_priority(self, prompt_manager):
        """Test that additional data takes priority over user_state."""
        template = "Hello {{name}}"
        result = prompt_manager._replace_template_params(
            template, data={"name": "OverrideName"}
        )

        assert result == "Hello OverrideName"


class TestBuildTemplateData:
    """Tests for _build_template_data method."""

    @pytest.fixture
    def prompt_manager(self):
        """Create a PromptManager instance for testing."""
        from super.core.voice.managers.prompt_manager import PromptManager

        config = {
            "system_prompt": "Test",
            "config_key": "config_value",
        }
        user_state = MockUserState(
            user_name="StateUser",
            contact_number="+9876543210",
            model_config={},
            extra_data={"extra_key": "extra_value"},
        )
        return PromptManager(
            config=config,
            agent_config=MockAgentConfig(),
            session_id="session-456",
            tool_calling=False,
            logger=logging.getLogger("test"),
            user_state=user_state,
        )

    def test_build_template_data_includes_session_id(self, prompt_manager):
        """Test that session_id is included in template data."""
        data = prompt_manager._build_template_data()
        assert data.get("session_id") == "session-456"

    def test_build_template_data_includes_config(self, prompt_manager):
        """Test that config values are included in template data."""
        data = prompt_manager._build_template_data()
        assert data.get("config_key") == "config_value"

    def test_build_template_data_includes_user_state(self, prompt_manager):
        """Test that user_state attributes are included."""
        data = prompt_manager._build_template_data()
        assert data.get("user_name") == "StateUser"
        assert data.get("contact_number") == "+9876543210"

    def test_build_template_data_includes_extra_data(self, prompt_manager):
        """Test that extra_data from user_state is included."""
        data = prompt_manager._build_template_data()
        assert data.get("extra_key") == "extra_value"

    def test_build_template_data_additional_data_priority(self, prompt_manager):
        """Test that additional_data has highest priority."""
        data = prompt_manager._build_template_data({"user_name": "OverrideUser"})
        assert data.get("user_name") == "OverrideUser"


class TestNullSafety:
    """Tests for null safety in template replacement."""

    def test_replace_with_none_user_state(self):
        """Test that replacement works when user_state is None."""
        from super.core.voice.managers.prompt_manager import PromptManager

        config = {"system_prompt": "Test", "name": "ConfigName"}
        pm = PromptManager(
            config=config,
            agent_config=MockAgentConfig(),
            session_id="test",
            tool_calling=False,
            logger=logging.getLogger("test"),
            user_state=None,
        )

        # Should not raise AttributeError
        result = pm._replace_template_params("Hello {{name}}")
        assert "ConfigName" in result

    def test_replace_with_empty_extra_data(self):
        """Test replacement when extra_data is empty."""
        from super.core.voice.managers.prompt_manager import PromptManager

        config = {"system_prompt": "Test", "name": "ConfigName"}
        user_state = MockUserState(
            user_name="User",
            model_config={},
            extra_data={},  # Empty extra_data
        )
        pm = PromptManager(
            config=config,
            agent_config=MockAgentConfig(),
            session_id="test",
            tool_calling=False,
            logger=logging.getLogger("test"),
            user_state=user_state,
        )

        result = pm._replace_template_params("Hello {{name}}")
        assert "ConfigName" in result


class TestRealWorldScenarios:
    """Tests with real-world template scenarios from production."""

    @pytest.fixture
    def prompt_manager_tata_capital(self):
        """Create PromptManager with Tata Capital OVD scenario data."""
        from super.core.voice.managers.prompt_manager import PromptManager

        config = {
            "system_prompt": "You are Ahaana from Tata Capital",
            "first_message": "Hello {{name}}, this is regarding your {{product}}",
            "use_conversational_prompts": False,
        }
        user_state = MockUserState(
            user_name="Customer",
            model_config={"follow_up_enabled": False, "enable_memory": False},
            extra_data={
                "user_data": {
                    "name": "Priya Sharma",
                    "product": "Personal Loan",
                    "last_digit": "9876",
                    "CUSTOMER_CARE_NUMBER": "1860-267-6060",
                    "doc_status": "not_submitted",
                    "city": "Mumbai",
                    "pincode": "400001",
                }
            },
        )
        return PromptManager(
            config=config,
            agent_config=MockAgentConfig(),
            session_id="tata-session",
            tool_calling=False,
            logger=logging.getLogger("test"),
            user_state=user_state,
        )

    def test_tata_capital_greeting_template(self, prompt_manager_tata_capital):
        """Test Tata Capital greeting template replacement."""
        template = (
            'Hello, this is Ahaana calling from Tata Capital. '
            'Am I speaking with {{name}}?'
        )
        result = prompt_manager_tata_capital._replace_template_params(template)

        assert "Priya Sharma" in result
        assert "{{name}}" not in result

    def test_tata_capital_loan_details_template(self, prompt_manager_tata_capital):
        """Test loan details template with multiple variables."""
        template = (
            "This call is regarding the recent {{product}} you have taken "
            "from Tata Capital which has loan ID ending with {{last_digit}}."
        )
        result = prompt_manager_tata_capital._replace_template_params(template)

        assert "Personal Loan" in result
        assert "9876" in result
        assert "{{product}}" not in result
        assert "{{last_digit}}" not in result

    def test_tata_capital_customer_care_template(self, prompt_manager_tata_capital):
        """Test customer care number template."""
        template = (
            "If you face any issue, please reach out to customer care "
            "at {{CUSTOMER_CARE_NUMBER}}."
        )
        result = prompt_manager_tata_capital._replace_template_params(template)

        assert "1860-267-6060" in result
        assert "{{CUSTOMER_CARE_NUMBER}}" not in result

    def test_tata_capital_full_script_template(self, prompt_manager_tata_capital):
        """Test a full script template with multiple variables."""
        template = """Hello {{name}}, this is Ahaana from Tata Capital.
Your {{product}} application with loan ID ending {{last_digit}} requires KYC documents.
Your city: {{city}}, Pincode: {{pincode}}.
For support, call {{CUSTOMER_CARE_NUMBER}}."""

        result = prompt_manager_tata_capital._replace_template_params(template)

        # All variables should be replaced
        assert "Priya Sharma" in result
        assert "Personal Loan" in result
        assert "9876" in result
        assert "Mumbai" in result
        assert "400001" in result
        assert "1860-267-6060" in result

        # No template markers should remain
        assert "{{" not in result
        assert "}}" not in result


class TestEdgeCases:
    """Tests for edge cases in template replacement."""

    @pytest.fixture
    def prompt_manager(self):
        """Create a basic PromptManager for edge case testing."""
        from super.core.voice.managers.prompt_manager import PromptManager

        config = {"system_prompt": "Test"}
        user_state = MockUserState(
            user_name="User",
            model_config={},
            extra_data={"user_data": {"name": "TestName", "number": 12345}},
        )
        return PromptManager(
            config=config,
            agent_config=MockAgentConfig(),
            session_id="test",
            tool_calling=False,
            logger=logging.getLogger("test"),
            user_state=user_state,
        )

    def test_numeric_value_replacement(self, prompt_manager):
        """Test that numeric values are converted to strings."""
        template = "Your number is {{number}}"
        result = prompt_manager._replace_template_params(template)
        assert result == "Your number is 12345"

    def test_whitespace_in_variable_name(self, prompt_manager):
        """Test handling of whitespace in variable names."""
        # Add data with whitespace-trimmed key
        prompt_manager.user_state.extra_data["user_data"]["spaced_key"] = "SpacedValue"
        template = "Value: {{ spaced_key }}"
        result = prompt_manager._replace_template_params(template)
        # Should handle whitespace in template markers
        assert "SpacedValue" in result or "{{ spaced_key }}" in result

    def test_special_characters_in_value(self, prompt_manager):
        """Test replacement of values with special characters."""
        prompt_manager.user_state.extra_data["user_data"]["special"] = "Test & <value>"
        template = "Special: {{special}}"
        result = prompt_manager._replace_template_params(template)
        assert "Test & <value>" in result

    def test_unicode_value_replacement(self, prompt_manager):
        """Test replacement with Unicode values."""
        prompt_manager.user_state.extra_data["user_data"]["hindi"] = "नमस्ते"
        template = "Greeting: {{hindi}}"
        result = prompt_manager._replace_template_params(template)
        assert "नमस्ते" in result

    def test_empty_string_value(self, prompt_manager):
        """Test replacement with empty string value."""
        prompt_manager.user_state.extra_data["user_data"]["empty"] = ""
        template = "Empty: {{empty}}"
        result = prompt_manager._replace_template_params(template)
        # Empty string is a valid value, should be replaced
        assert result == "Empty: " or "{{empty}}" in result
