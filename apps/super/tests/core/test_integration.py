"""
Integration tests for the ReAct Orchestrator system.

Tests the full stack:
- Central tools with ToolRegistry
- Handler hierarchy (ToolCallHandler, ReActHandler, PlanningHandler)
- ReActOrc with LangGraph
- Adapter compatibility
"""

from typing import Any, Dict

import pytest

from super.core.handler.planning_handler import PlanningHandler
from super.core.handler.react_handler import ActionType, ReActHandler, Thought
from super.core.handler.tool_handler import ToolCallHandler
from super.core.orchestrator.react_orc import AgentState, ReActConfig, ReActOrc
from super.core.tools import (
    BaseTool,
    BookingStore,
    CancelBookingTool,
    ConfirmBookingTool,
    CreateBookingTool,
    ToolCategory,
    ToolRegistry,
    ToolResult,
)
from super.core.tools.adapters import (
    CentralToolPlugin,
    create_superkik_compatible_registry,
)


class CalculatorTool(BaseTool):
    """Calculator tool for integration tests."""

    name = "calculate"
    description = "Perform arithmetic operations"
    category = ToolCategory.UTILITY

    async def execute(
        self, operation: str = "add", x: int = 0, y: int = 0
    ) -> ToolResult:
        ops = {
            "add": x + y,
            "subtract": x - y,
            "multiply": x * y,
            "divide": x / y if y != 0 else 0,
        }
        result = ops.get(operation, 0)
        return ToolResult(success=True, data={"result": result, "operation": operation})

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["add", "subtract", "multiply", "divide"],
                    },
                    "x": {"type": "integer"},
                    "y": {"type": "integer"},
                },
                "required": ["operation", "x", "y"],
            },
        }


class WeatherTool(BaseTool):
    """Mock weather tool for integration tests."""

    name = "get_weather"
    description = "Get weather for a location"
    category = ToolCategory.SEARCH

    async def execute(self, location: str = "") -> ToolResult:
        mock_weather = {
            "new york": {"temp": 72, "condition": "sunny"},
            "london": {"temp": 55, "condition": "cloudy"},
            "tokyo": {"temp": 68, "condition": "rainy"},
        }

        weather = mock_weather.get(location.lower())
        if weather:
            return ToolResult(
                success=True,
                data={"location": location, **weather},
            )
        return ToolResult(
            success=True,
            data={"location": location, "temp": 65, "condition": "unknown"},
        )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {"location": {"type": "string"}},
                "required": ["location"],
            },
        }


class TestToolRegistryIntegration:
    """Integration tests for ToolRegistry with multiple tools."""

    @pytest.fixture
    def registry(self) -> ToolRegistry:
        reg = ToolRegistry()
        reg.register(CalculatorTool())
        reg.register(WeatherTool())
        return reg

    @pytest.mark.anyio
    async def test_multiple_tool_execution(self, registry: ToolRegistry) -> None:
        calc_result = await registry.execute("calculate", operation="multiply", x=7, y=8)
        assert calc_result.success is True
        assert calc_result.data["result"] == 56

        weather_result = await registry.execute("get_weather", location="Tokyo")
        assert weather_result.success is True
        assert weather_result.data["condition"] == "rainy"

    def test_schema_collection(self, registry: ToolRegistry) -> None:
        schemas = registry.get_all_schemas()
        assert len(schemas) == 2
        names = {s["name"] for s in schemas}
        assert names == {"calculate", "get_weather"}


class TestHandlerWithToolsIntegration:
    """Integration tests for handlers with tool execution."""

    @pytest.fixture
    def handler(self) -> ToolCallHandler:
        h = ToolCallHandler()
        h.register_tool(CalculatorTool())
        h.register_tool(WeatherTool())
        return h

    @pytest.mark.anyio
    async def test_sequential_tool_calls(self, handler: ToolCallHandler) -> None:
        r1 = await handler.call_tool("calculate", operation="add", x=10, y=20)
        assert r1.data["result"] == 30

        r2 = await handler.call_tool("calculate", operation="multiply", x=5, y=6)
        assert r2.data["result"] == 30

        history = handler.get_tool_call_history()
        assert len(history) == 2
        assert history[0]["tool"] == "calculate"
        assert history[1]["tool"] == "calculate"


class TestReActHandlerIntegration:
    """Integration tests for ReActHandler with custom think function."""

    @pytest.mark.anyio
    async def test_react_with_tool_loop(self) -> None:
        handler = ReActHandler(max_iterations=5)
        handler.register_tool(CalculatorTool())

        iteration_count = 0

        original_think = handler.think

        async def custom_think(context):
            nonlocal iteration_count
            iteration_count += 1

            if iteration_count == 1:
                return Thought(
                    reasoning="First, calculate 5 + 3",
                    next_action=ActionType.TOOL_CALL,
                    tool_name="calculate",
                    tool_params={"operation": "add", "x": 5, "y": 3},
                )
            elif iteration_count == 2:
                last_obs = context.observations[-1] if context.observations else None
                if last_obs and last_obs.success:
                    return Thought(
                        reasoning=f"Got result {last_obs.data}, now responding",
                        next_action=ActionType.RESPOND,
                        response_content=f"The answer is {last_obs.data['result']}",
                    )
            return Thought(
                reasoning="Done",
                next_action=ActionType.RESPOND,
                response_content="Task complete",
            )

        handler.think = custom_think

        result = await handler.execute("Calculate 5 + 3")

        assert result["final_response"] == "The answer is 8"
        assert len(result["tool_calls"]) == 1
        assert result["tool_calls"][0]["tool"] == "calculate"


class TestBookingFlowIntegration:
    """Integration tests for complete booking flow."""

    @pytest.fixture
    def booking_handler(self) -> ToolCallHandler:
        store = BookingStore()
        h = ToolCallHandler()
        h.register_tool(CreateBookingTool(store=store))
        h.register_tool(ConfirmBookingTool(store=store))
        h.register_tool(CancelBookingTool(store=store))
        return h

    @pytest.mark.anyio
    async def test_complete_booking_flow(self, booking_handler: ToolCallHandler) -> None:
        create_result = await booking_handler.call_tool(
            "create_booking",
            provider_id="provider_123",
            provider_name="Dr. Smith",
            time_slot="Tomorrow 10am",
            service_type="Checkup",
        )
        assert create_result.success is True
        booking_id = create_result.data["booking_id"]

        confirm_result = await booking_handler.call_tool(
            "confirm_booking",
            booking_id=booking_id,
        )
        assert confirm_result.success is True
        assert confirm_result.data["status"] == "confirmed"
        assert "confirmation_code" in confirm_result.data

    @pytest.mark.anyio
    async def test_booking_cancellation_flow(
        self, booking_handler: ToolCallHandler
    ) -> None:
        create_result = await booking_handler.call_tool(
            "create_booking",
            provider_id="provider_456",
            provider_name="Dr. Jones",
        )
        booking_id = create_result.data["booking_id"]

        cancel_result = await booking_handler.call_tool(
            "cancel_booking",
            booking_id=booking_id,
            reason="Schedule conflict",
        )
        assert cancel_result.success is True
        assert cancel_result.data["status"] == "cancelled"


class TestReActOrcIntegration:
    """Integration tests for ReActOrc with LangGraph."""

    @pytest.mark.anyio
    async def test_orc_with_custom_thinking(self) -> None:
        def smart_think(state: AgentState) -> Thought:
            if not state["observations"]:
                return Thought(
                    reasoning="Need to get weather first",
                    next_action=ActionType.TOOL_CALL,
                    tool_name="get_weather",
                    tool_params={"location": "New York"},
                )
            else:
                last_obs = state["observations"][-1]
                if last_obs.get("success"):
                    data = last_obs.get("data", {})
                    return Thought(
                        reasoning="Got weather data",
                        next_action=ActionType.RESPOND,
                        response_content=(
                            f"Weather in {data.get('location')}: "
                            f"{data.get('temp')}°F, {data.get('condition')}"
                        ),
                    )
            return Thought(
                reasoning="Default response",
                next_action=ActionType.RESPOND,
                response_content="Could not get weather",
            )

        config = ReActConfig(max_iterations=5)
        orc = ReActOrc(config=config)
        orc.register_tool(WeatherTool())
        orc.set_think_fn(smart_think)

        result = await orc.execute("What's the weather in New York?")

        assert result["status"] == "success"
        assert "72°F" in result["final_response"]
        assert "sunny" in result["final_response"]
        assert len(result["tool_calls"]) == 1

    @pytest.mark.anyio
    async def test_orc_with_callbacks(self) -> None:
        thoughts_received = []
        tool_calls_received = []

        def thought_callback(t: Thought) -> None:
            thoughts_received.append(t)

        def tool_callback(name: str, params: Dict, result: ToolResult) -> None:
            tool_calls_received.append({"name": name, "params": params})

        config = ReActConfig(
            max_iterations=3,
            thinking_callback=thought_callback,
            tool_call_callback=tool_callback,
        )

        def calc_think(state: AgentState) -> Thought:
            if not state["observations"]:
                return Thought(
                    reasoning="Calculate",
                    next_action=ActionType.TOOL_CALL,
                    tool_name="calculate",
                    tool_params={"operation": "multiply", "x": 12, "y": 12},
                )
            return Thought(
                reasoning="Done",
                next_action=ActionType.RESPOND,
                response_content="144",
            )

        orc = ReActOrc(config=config)
        orc.register_tool(CalculatorTool())
        orc.set_think_fn(calc_think)

        await orc.execute("12 squared")

        assert len(thoughts_received) >= 1
        assert len(tool_calls_received) == 1
        assert tool_calls_received[0]["name"] == "calculate"


class TestPlanningHandlerIntegration:
    """Integration tests for PlanningHandler with multi-step execution."""

    @pytest.mark.anyio
    async def test_planning_with_tools(self) -> None:
        handler = PlanningHandler(max_iterations=10)
        handler.register_tool(CalculatorTool())
        handler.register_tool(WeatherTool())

        result = await handler.execute("Complete a multi-step task")

        assert "plan" in result
        assert result["plan"]["is_complete"] is True


class TestAdapterIntegration:
    """Integration tests for adapter compatibility."""

    @pytest.mark.anyio
    async def test_central_plugin_with_real_tools(self) -> None:
        store = BookingStore()
        plugin = CentralToolPlugin(
            name="booking_tools",
            tools=[
                CreateBookingTool(store=store),
                ConfirmBookingTool(store=store),
            ],
        )

        await plugin.initialize(handler=None)

        functions = plugin.get_tool_functions()
        assert len(functions) == 2

        create_fn = functions[0]
        result = await create_fn(
            provider_id="test_provider",
            provider_name="Test Clinic",
            time_slot="Today 3pm",
        )

        import json

        data = json.loads(result)
        assert data["status"] == "success"
        assert "booking_id" in data["data"]

    @pytest.mark.anyio
    async def test_registry_to_plugin_conversion(self) -> None:
        registry = ToolRegistry()
        registry.register(CalculatorTool())
        registry.register(WeatherTool())

        plugin = create_superkik_compatible_registry(registry, "mixed_tools")
        await plugin.initialize(handler=None)

        assert len(plugin.get_tool_functions()) == 2
        assert plugin.get_metrics()["tool_count"] == 2


class TestFullStackIntegration:
    """End-to-end integration tests for the complete system."""

    @pytest.mark.anyio
    async def test_orc_with_booking_flow(self) -> None:
        store = BookingStore()

        def booking_flow_think(state: AgentState) -> Thought:
            iteration = len(state["thoughts"])

            if iteration == 0:
                return Thought(
                    reasoning="Create booking",
                    next_action=ActionType.TOOL_CALL,
                    tool_name="create_booking",
                    tool_params={
                        "provider_id": "doc_1",
                        "provider_name": "Dr. Smith",
                        "time_slot": "Monday 2pm",
                    },
                )
            elif iteration == 1:
                last_obs = state["observations"][-1]
                if last_obs.get("success"):
                    booking_id = last_obs.get("data", {}).get("booking_id")
                    return Thought(
                        reasoning="Confirm booking",
                        next_action=ActionType.TOOL_CALL,
                        tool_name="confirm_booking",
                        tool_params={"booking_id": booking_id},
                    )
            elif iteration == 2:
                last_obs = state["observations"][-1]
                if last_obs.get("success"):
                    code = last_obs.get("data", {}).get("confirmation_code")
                    return Thought(
                        reasoning="Booking confirmed",
                        next_action=ActionType.RESPOND,
                        response_content=f"Booking confirmed! Code: {code}",
                    )

            return Thought(
                reasoning="Done",
                next_action=ActionType.RESPOND,
                response_content="Booking flow complete",
            )

        orc = ReActOrc(config=ReActConfig(max_iterations=10))
        orc.register_tool(CreateBookingTool(store=store))
        orc.register_tool(ConfirmBookingTool(store=store))
        orc.set_think_fn(booking_flow_think)

        result = await orc.execute("Book appointment with Dr. Smith")

        assert result["status"] == "success"
        assert "confirmed" in result["final_response"].lower()
        assert len(result["tool_calls"]) == 2
