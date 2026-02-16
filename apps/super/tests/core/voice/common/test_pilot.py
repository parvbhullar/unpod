"""Tests for pilot lookup functions."""
import pytest
import sys
from unittest.mock import patch, MagicMock


# Mock mysql.connector before importing pilot module
mock_mysql = MagicMock()
sys.modules['mysql'] = mock_mysql
sys.modules['mysql.connector'] = MagicMock()
sys.modules['mysql.connector.pooling'] = MagicMock()
sys.modules['mysql.connector.errors'] = MagicMock()


class TestGetPilotSlug:
    """Tests for get_pilot_slug function."""

    def test_get_pilot_slug_uses_jsonb_query(self):
        """Should use PostgreSQL jsonb query syntax."""
        # Mock executeQuery in the db module
        with patch('super_services.libs.core.db.executeQuery') as mock_query:
            mock_query.return_value = [{"handle": "test-pilot"}]

            from super.core.voice.common.pilot import get_pilot_slug

            result = get_pilot_slug("+1234567890")

            # Check that executeQuery was called
            assert mock_query.called
            call_args = mock_query.call_args
            query = call_args[0][0] if call_args[0] else call_args[1].get('query', '')

            # Should NOT use MySQL JSON_SEARCH
            assert "JSON_SEARCH" not in query, "Should not use MySQL JSON_SEARCH"
            # Should use PostgreSQL jsonb syntax
            assert ("jsonb_array_elements" in query or "->>" in query), \
                "Should use PostgreSQL jsonb syntax (jsonb_array_elements or ->>)"
            assert result == "test-pilot"


class TestGetPilotFromAssistantId:
    """Tests for get_pilot_from_assistant_id function."""

    def test_uses_jsonb_extract(self):
        """Should use PostgreSQL jsonb extraction."""
        # Need to reload the module after patching to get the right import
        import importlib
        import super.core.voice.common.pilot as pilot_module

        with patch.object(pilot_module, 'executeQuery') as mock_query:
            mock_query.return_value = [{"handle": "test-pilot"}]

            # Reload to get fresh reference
            importlib.reload(pilot_module)

            # Now patch again on the reloaded module
            with patch.object(pilot_module, 'executeQuery') as mock_query2:
                mock_query2.return_value = [{"handle": "test-pilot"}]

                result = pilot_module.get_pilot_from_assistant_id("assistant-123")

                assert mock_query2.called, "executeQuery should be called"
                call_args = mock_query2.call_args
                query = call_args[1].get('query', '') if call_args[1] else call_args[0][0]

                # Should NOT use MySQL JSON_UNQUOTE/JSON_EXTRACT
                assert "JSON_UNQUOTE" not in query, "Should not use MySQL JSON_UNQUOTE"
                assert "JSON_EXTRACT" not in query, "Should not use MySQL JSON_EXTRACT"
                # Should use PostgreSQL jsonb syntax
                assert "->>" in query, "Should use PostgreSQL ->> operator for jsonb extraction"
                assert result == "test-pilot"
