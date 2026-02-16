"""Tests for central tools (places, booking, telephony)."""

import pytest

from super.core.tools.base import ToolCategory, ToolRegistry
from super.core.tools.booking import (
    BookingStatusType,
    BookingStore,
    CancelBookingTool,
    ConfirmBookingTool,
    CreateBookingTool,
)
from super.core.tools.places import PlacesTool
from super.core.tools.telephony import (
    CallManager,
    CallStatusType,
    EndCallTool,
    GetCallStatusTool,
    InitiateCallTool,
)


class TestPlacesTool:
    """Tests for PlacesTool."""

    def test_tool_properties(self) -> None:
        tool = PlacesTool()
        assert tool.name == "search_places"
        assert tool.category == ToolCategory.SEARCH

    def test_schema(self) -> None:
        tool = PlacesTool()
        schema = tool.get_schema()
        assert schema["name"] == "search_places"
        assert "query" in schema["parameters"]["properties"]
        assert "query" in schema["parameters"]["required"]


class TestBookingTools:
    """Tests for booking tools."""

    @pytest.fixture
    def store(self) -> BookingStore:
        return BookingStore()

    @pytest.mark.anyio
    async def test_create_booking(self, store: BookingStore) -> None:
        tool = CreateBookingTool(store=store)
        result = await tool.execute(
            provider_id="p1",
            provider_name="Test Clinic",
            time_slot="tomorrow 10am",
            service_type="checkup",
        )

        assert result.success is True
        assert "booking_id" in result.data
        assert result.data["provider_name"] == "Test Clinic"
        assert result.data["status"] == BookingStatusType.PENDING.value

    @pytest.mark.anyio
    async def test_confirm_booking(self, store: BookingStore) -> None:
        create_tool = CreateBookingTool(store=store)
        create_result = await create_tool.execute(
            provider_id="p1",
            provider_name="Test Clinic",
        )
        booking_id = create_result.data["booking_id"]

        confirm_tool = ConfirmBookingTool(store=store)
        result = await confirm_tool.execute(booking_id=booking_id)

        assert result.success is True
        assert result.data["status"] == BookingStatusType.CONFIRMED.value
        assert "confirmation_code" in result.data

    @pytest.mark.anyio
    async def test_confirm_nonexistent_booking(self, store: BookingStore) -> None:
        tool = ConfirmBookingTool(store=store)
        result = await tool.execute(booking_id="nonexistent")

        assert result.success is False
        assert "not found" in result.error

    @pytest.mark.anyio
    async def test_cancel_booking(self, store: BookingStore) -> None:
        create_tool = CreateBookingTool(store=store)
        create_result = await create_tool.execute(
            provider_id="p1",
            provider_name="Test Clinic",
        )
        booking_id = create_result.data["booking_id"]

        cancel_tool = CancelBookingTool(store=store)
        result = await cancel_tool.execute(booking_id=booking_id, reason="Changed plans")

        assert result.success is True
        assert result.data["status"] == BookingStatusType.CANCELLED.value

    @pytest.mark.anyio
    async def test_double_cancel(self, store: BookingStore) -> None:
        create_tool = CreateBookingTool(store=store)
        create_result = await create_tool.execute(
            provider_id="p1",
            provider_name="Test Clinic",
        )
        booking_id = create_result.data["booking_id"]

        cancel_tool = CancelBookingTool(store=store)
        await cancel_tool.execute(booking_id=booking_id)
        result = await cancel_tool.execute(booking_id=booking_id)

        assert result.success is False


class TestTelephonyTools:
    """Tests for telephony tools."""

    @pytest.fixture
    def manager(self) -> CallManager:
        return CallManager()

    @pytest.mark.anyio
    async def test_initiate_call(self, manager: CallManager) -> None:
        tool = InitiateCallTool(manager=manager)
        result = await tool.execute(
            provider_id="p1",
            provider_name="Test Clinic",
            phone_number="+1234567890",
            objective="Book appointment",
        )

        assert result.success is True
        assert "call_id" in result.data
        assert result.data["provider_name"] == "Test Clinic"

    @pytest.mark.anyio
    async def test_call_already_active(self, manager: CallManager) -> None:
        tool = InitiateCallTool(manager=manager)
        await tool.execute(
            provider_id="p1",
            provider_name="First Clinic",
            phone_number="+1234567890",
        )

        result = await tool.execute(
            provider_id="p2",
            provider_name="Second Clinic",
            phone_number="+0987654321",
        )

        assert result.success is True
        assert result.metadata.get("already_active") is True
        assert result.data["provider_name"] == "First Clinic"

    @pytest.mark.anyio
    async def test_end_call(self, manager: CallManager) -> None:
        init_tool = InitiateCallTool(manager=manager)
        await init_tool.execute(
            provider_id="p1",
            provider_name="Test Clinic",
            phone_number="+1234567890",
        )

        end_tool = EndCallTool(manager=manager)
        result = await end_tool.execute()

        assert result.success is True
        assert result.data["status"] == CallStatusType.ENDED.value
        assert "duration_seconds" in result.data

    @pytest.mark.anyio
    async def test_end_no_active_call(self, manager: CallManager) -> None:
        tool = EndCallTool(manager=manager)
        result = await tool.execute()

        assert result.success is False
        assert "No active call" in result.error

    @pytest.mark.anyio
    async def test_get_call_status(self, manager: CallManager) -> None:
        init_tool = InitiateCallTool(manager=manager)
        await init_tool.execute(
            provider_id="p1",
            provider_name="Test Clinic",
            phone_number="+1234567890",
        )

        status_tool = GetCallStatusTool(manager=manager)
        result = await status_tool.execute()

        assert result.success is True
        assert result.data["provider_name"] == "Test Clinic"

    @pytest.mark.anyio
    async def test_get_call_status_no_call(self, manager: CallManager) -> None:
        tool = GetCallStatusTool(manager=manager)
        result = await tool.execute()

        assert result.success is True
        assert result.data["status"] == "no_call"


class TestToolRegistry:
    """Tests for ToolRegistry with new tools."""

    @pytest.mark.anyio
    async def test_register_and_execute(self) -> None:
        registry = ToolRegistry()
        store = BookingStore()
        registry.register(CreateBookingTool(store=store))
        registry.register(ConfirmBookingTool(store=store))

        create_result = await registry.execute(
            "create_booking",
            provider_id="p1",
            provider_name="Test Clinic",
        )

        assert create_result.success is True
        booking_id = create_result.data["booking_id"]

        confirm_result = await registry.execute(
            "confirm_booking",
            booking_id=booking_id,
        )

        assert confirm_result.success is True

    def test_get_tools_by_category(self) -> None:
        registry = ToolRegistry()
        registry.register(PlacesTool())
        registry.register(CreateBookingTool())
        registry.register(InitiateCallTool())

        search_tools = registry.get_tools_by_category(ToolCategory.SEARCH)
        assert len(search_tools) == 1
        assert search_tools[0].name == "search_places"

        booking_tools = registry.get_tools_by_category(ToolCategory.BOOKING)
        assert len(booking_tools) == 1
        assert booking_tools[0].name == "create_booking"
