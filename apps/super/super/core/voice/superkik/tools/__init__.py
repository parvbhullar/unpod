"""
SuperKik Tools - Dynamic tool plugin system for voice agents.

Provides a plugin-based architecture for registering LLM-invocable tools:
- PlacesToolPlugin: Search for providers (Google Places API)
- TelephonyToolPlugin: Call management (SIP telephony)
- BookingToolPlugin: Appointment booking
- ExaToolPlugin: Web search and people discovery (Exa AI)
- CallsToolPlugin: CSV-based call task creation

Usage:
    from super.core.voice.superkik.tools import ToolPluginRegistry

    registry = ToolPluginRegistry()
    await registry.activate_from_config(handler, config)
    tools = registry.get_all_tool_functions()
"""

from super.core.voice.superkik.tools.base import (
    ToolPlugin,
    ToolPluginConfig,
    ToolPluginRegistry,
)
from super.core.voice.superkik.tools.booking import (
    BookingToolPlugin,
    cancel_booking_impl,
    confirm_booking_impl,
    create_booking_impl,
    get_booking_status_impl,
)
from super.core.voice.superkik.tools.calls import (
    CallsToolPlugin,
    ExecuteRunResult,
    create_call_run_impl,
    execute_call_run_impl,
    parse_csv_content,
    process_csv_for_calls_impl,
    reject_call_run_impl,
)
from super.core.voice.superkik.tools.exa import (
    ExaToolPlugin,
    create_research_impl,
    get_research_impl,
    search_people_impl,
    search_web_impl,
)
from super.core.voice.superkik.tools.places import (
    PlacesToolPlugin,
    get_provider_details_impl,
    search_providers_impl,
)
from super.core.voice.superkik.tools.telephony import (
    TelephonyToolPlugin,
    end_call_impl,
    get_call_status_impl,
    initiate_call_impl,
)

__all__ = [
    # Base classes
    "ToolPlugin",
    "ToolPluginConfig",
    "ToolPluginRegistry",
    # Tool plugins
    "PlacesToolPlugin",
    "TelephonyToolPlugin",
    "BookingToolPlugin",
    "ExaToolPlugin",
    "CallsToolPlugin",
    # Places implementation functions
    "search_providers_impl",
    "get_provider_details_impl",
    # Telephony implementation functions
    "initiate_call_impl",
    "end_call_impl",
    "get_call_status_impl",
    # Booking implementation functions
    "create_booking_impl",
    "confirm_booking_impl",
    "cancel_booking_impl",
    "get_booking_status_impl",
    # Exa implementation functions
    "search_web_impl",
    "search_people_impl",
    "create_research_impl",
    "get_research_impl",
    # Calls implementation functions
    "process_csv_for_calls_impl",
    "create_call_run_impl",
    "execute_call_run_impl",
    "reject_call_run_impl",
    "parse_csv_content",
    "ExecuteRunResult",
]
