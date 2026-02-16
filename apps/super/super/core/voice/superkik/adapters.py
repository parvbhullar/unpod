"""
Adapters for bridging ToolPlugin to superkik tool format.

Converts LiveKit function_tool decorated functions to superkik ToolDefinition
and async handlers for use with the superkik agentic backbone.
"""

from __future__ import annotations

import inspect
import json
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    get_args,
    get_origin,
)

from pydantic import Field
from pydantic.fields import FieldInfo

if TYPE_CHECKING:
    from super.core.voice.superkik.tools.base import ToolPlugin, ToolPluginRegistry

# Type alias for superkik tool handler
ToolHandler = Callable[[Dict[str, Any]], Awaitable[str]]


def _get_annotation_field_info(annotation: Any) -> Optional[FieldInfo]:
    """Extract FieldInfo from Annotated type if present."""
    origin = get_origin(annotation)
    if origin is not None:
        # Handle Annotated types
        args = get_args(annotation)
        for arg in args:
            if isinstance(arg, FieldInfo):
                return arg
    return None


def _get_base_type(annotation: Any) -> type:
    """Get the base type from an annotation (unwrap Annotated, Optional, etc)."""
    origin = get_origin(annotation)

    if origin is None:
        return annotation if isinstance(annotation, type) else str

    # Handle Annotated[T, ...]
    args = get_args(annotation)
    if args:
        # For Annotated, first arg is the actual type
        first_arg = args[0]
        # Recursively unwrap
        return _get_base_type(first_arg)

    return str


def _python_type_to_json_schema_type(py_type: type) -> str:
    """Map Python type to JSON Schema type string."""
    type_map = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
        type(None): "string",
    }
    return type_map.get(py_type, "string")


def extract_tool_schema(func: Callable) -> Dict[str, Any]:
    """
    Extract JSON schema from a function's type annotations.

    Handles:
    - Annotated types with Field metadata
    - Optional types
    - Default values

    Returns:
        Dict with 'name', 'description', 'parameters' (JSON schema format)
    """
    sig = inspect.signature(func)
    hints = getattr(func, "__annotations__", {})
    doc = func.__doc__ or f"Tool: {func.__name__}"

    # Build parameters schema
    properties: Dict[str, Any] = {}
    required: List[str] = []

    for param_name, param in sig.parameters.items():
        # Skip context parameter (first param in function_tool)
        if param_name in ("context", "self", "cls"):
            continue

        annotation = hints.get(param_name, str)
        field_info = _get_annotation_field_info(annotation)
        base_type = _get_base_type(annotation)

        # Build property schema
        prop_schema: Dict[str, Any] = {
            "type": _python_type_to_json_schema_type(base_type),
        }

        # Add description from Field or default
        if field_info and field_info.description:
            prop_schema["description"] = field_info.description
        else:
            prop_schema["description"] = f"Parameter: {param_name}"

        # Check if required
        has_default = param.default is not inspect.Parameter.empty
        is_optional = get_origin(annotation) is type(None) or (
            get_origin(annotation) is not None
            and type(None) in get_args(annotation)
        )

        if not has_default and not is_optional:
            required.append(param_name)

        properties[param_name] = prop_schema

    return {
        "name": func.__name__,
        "description": doc.strip().split("\n")[0],
        "parameters": {
            "type": "object",
            "properties": properties,
            "required": required,
        },
    }


def create_tool_handler(
    func: Callable,
    plugin: "ToolPlugin",
) -> ToolHandler:
    """
    Create an async handler that wraps a function_tool function.

    The handler:
    1. Accepts args dict from superkik
    2. Calls the original function with unpacked args
    3. Returns JSON string result

    Args:
        func: The @function_tool decorated function
        plugin: The ToolPlugin instance (for handler reference)

    Returns:
        Async handler compatible with superkik
    """

    async def handler(args: Dict[str, Any]) -> str:
        try:
            # Create a mock RunContext (function_tool expects this as first arg)
            # In superkik mode, we don't use LiveKit's RunContext
            class MockContext:
                pass

            context = MockContext()

            # Call the function
            result = await func(context, **args)

            # Serialize result
            if isinstance(result, dict):
                return json.dumps(result)
            elif result is None:
                return json.dumps({"success": True})
            else:
                return str(result)

        except Exception as e:
            return json.dumps({"error": str(e), "success": False})

    return handler


def adapt_function_tool(
    func: Callable,
    plugin: "ToolPlugin",
) -> Tuple[Dict[str, Any], ToolHandler]:
    """
    Adapt a @function_tool decorated function to superkik format.

    Args:
        func: The @function_tool decorated function
        plugin: The ToolPlugin instance

    Returns:
        Tuple of (tool_definition_dict, handler)
    """
    schema = extract_tool_schema(func)
    handler = create_tool_handler(func, plugin)
    return schema, handler


def adapt_tool_plugin(
    plugin: "ToolPlugin",
) -> List[Tuple[Dict[str, Any], ToolHandler]]:
    """
    Adapt all tools from a ToolPlugin to superkik format.

    Args:
        plugin: The ToolPlugin instance with initialized tools

    Returns:
        List of (tool_definition_dict, handler) tuples
    """
    results: List[Tuple[Dict[str, Any], ToolHandler]] = []

    for func in plugin.get_tool_functions():
        try:
            schema, handler = adapt_function_tool(func, plugin)
            results.append((schema, handler))
        except Exception as e:
            # Log but continue with other tools
            plugin._logger.warning(
                f"Failed to adapt tool {getattr(func, '__name__', 'unknown')}: {e}"
            )

    return results


def adapt_registry(
    registry: "ToolPluginRegistry",
) -> Tuple[List[Dict[str, Any]], Dict[str, ToolHandler]]:
    """
    Adapt all tools from a ToolPluginRegistry to superkik format.

    Args:
        registry: The ToolPluginRegistry with activated plugins

    Returns:
        Tuple of (list of tool definitions, dict of name -> handler)
    """
    definitions: List[Dict[str, Any]] = []
    handlers: Dict[str, ToolHandler] = {}

    for plugin in registry._instances.values():
        if not plugin.enabled:
            continue

        adapted = adapt_tool_plugin(plugin)
        for schema, handler in adapted:
            definitions.append(schema)
            handlers[schema["name"]] = handler

    return definitions, handlers
