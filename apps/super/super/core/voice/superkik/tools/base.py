"""
Tool Plugin System for SuperKik.

Provides a dynamic plugin architecture for registering and managing
voice agent tools. Follows the same patterns as PipelinePlugin/PluginRegistry.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Type,
)
import logging

if TYPE_CHECKING:
    from super.core.voice.superkik.handler import SuperKikHandler


@dataclass
class ToolPluginConfig:
    """Configuration for a tool plugin."""

    enabled: bool = True
    options: Dict[str, Any] = field(default_factory=dict)


class ToolPlugin(ABC):
    """
    Base class for SuperKik tool plugins.

    Tool plugins provide LLM function tools that can be dynamically
    registered with the voice agent. Each plugin can provide multiple
    related tools (e.g., PlacesToolPlugin provides search and details).

    Example:
        class MyToolPlugin(ToolPlugin):
            name = "my_tools"

            def get_tool_functions(self) -> List[Callable]:
                return [self._create_my_tool()]

            def _create_my_tool(self):
                @function_tool
                async def my_tool(context: RunContext, param: str) -> str:
                    return await my_tool_impl(self._handler, param)
                return my_tool
    """

    name: str = "base_tool"

    def __init__(
        self,
        config: Optional[ToolPluginConfig] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self._config = config or ToolPluginConfig()
        self._logger = logger or logging.getLogger(f"tool.{self.name}")
        self._handler: Optional["SuperKikHandler"] = None
        self._initialized = False
        self._tool_functions: List[Callable] = []

    @property
    def enabled(self) -> bool:
        """Check if plugin is enabled."""
        return self._config.enabled

    @property
    def options(self) -> Dict[str, Any]:
        """Get plugin options."""
        return self._config.options

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable the plugin at runtime."""
        self._config.enabled = enabled
        self._logger.info(
            f"Tool plugin {self.name} {'enabled' if enabled else 'disabled'}"
        )

    async def initialize(self, handler: "SuperKikHandler") -> None:
        """
        Initialize the plugin with handler reference.

        Called when plugin is activated. Creates tool functions bound to handler.

        Args:
            handler: The SuperKikHandler instance
        """
        self._handler = handler
        self._tool_functions = self._create_tools()
        self._initialized = True
        self._logger.debug(
            f"Tool plugin {self.name} initialized with {len(self._tool_functions)} tools"
        )

    @abstractmethod
    def _create_tools(self) -> List[Callable]:
        """
        Create and return tool functions.

        Override to create @function_tool decorated functions bound to self._handler.

        Returns:
            List of function_tool decorated callables
        """
        ...

    def get_tool_functions(self) -> List[Callable]:
        """
        Return list of tool functions for agent registration.

        Returns:
            List of @function_tool decorated functions
        """
        if not self._initialized:
            self._logger.warning(f"Tool plugin {self.name} not initialized")
            return []

        if not self.enabled:
            return []

        return self._tool_functions

    def get_tool_names(self) -> List[str]:
        """Get names of all tools provided by this plugin."""
        return [f.__name__ for f in self._tool_functions]

    async def cleanup(self) -> None:
        """Clean up plugin resources."""
        self._tool_functions = []
        self._initialized = False
        self._handler = None
        self._logger.debug(f"Tool plugin {self.name} cleaned up")

    def get_metrics(self) -> Optional[Dict[str, Any]]:
        """
        Return plugin metrics for observability.

        Override to provide timing/count metrics.

        Returns:
            Dict with metric names and values, or None
        """
        return None

    def __repr__(self) -> str:
        status = "enabled" if self.enabled else "disabled"
        tool_count = len(self._tool_functions)
        return (
            f"{self.__class__.__name__}(name={self.name}, tools={tool_count}, {status})"
        )


class ToolPluginRegistry:
    """
    Registry for managing tool plugins.

    Handles registration, activation, and lifecycle of tool plugins.
    Mirrors the PluginRegistry pattern for consistency.

    Example:
        registry = ToolPluginRegistry()
        await registry.activate_from_config(handler, config)
        tools = registry.get_all_tool_functions()
    """

    # Built-in tool plugin classes (lazy imports)
    _builtin_plugins: Dict[str, str] = {
        "places": "super.core.voice.superkik.tools.places.PlacesToolPlugin",
        "booking": "super.core.voice.superkik.tools.booking.BookingToolPlugin",
        "telephony": "super.core.voice.superkik.tools.telephony.TelephonyToolPlugin",
        "exa": "super.core.voice.superkik.tools.exa.ExaToolPlugin",
        "calls": "super.core.voice.superkik.tools.calls.CallsToolPlugin",
    }

    def __init__(self, logger: Optional[logging.Logger] = None):
        self._logger = logger or logging.getLogger("tool.registry")
        self._registered: Dict[str, Type[ToolPlugin]] = {}
        self._instances: Dict[str, ToolPlugin] = {}
        self._activated: Set[str] = set()

    def register(
        self,
        plugin_class: Type[ToolPlugin],
        name: Optional[str] = None,
    ) -> None:
        """
        Register a tool plugin class.

        Args:
            plugin_class: The plugin class to register
            name: Optional name override (defaults to plugin_class.name)
        """
        plugin_name = name or plugin_class.name
        self._registered[plugin_name] = plugin_class
        self._logger.debug(f"Registered tool plugin: {plugin_name}")

    def _load_builtin(self, name: str) -> Optional[Type[ToolPlugin]]:
        """Load a built-in plugin class by name."""
        if name not in self._builtin_plugins:
            return None

        module_path = self._builtin_plugins[name]
        try:
            module_name, class_name = module_path.rsplit(".", 1)
            module = __import__(module_name, fromlist=[class_name])
            plugin_class = getattr(module, class_name)
            self._registered[name] = plugin_class
            return plugin_class
        except (ImportError, AttributeError) as e:
            self._logger.warning(f"Failed to load builtin tool plugin {name}: {e}")
            return None

    async def activate(
        self,
        name: str,
        handler: "SuperKikHandler",
        config: Optional[ToolPluginConfig] = None,
    ) -> Optional[ToolPlugin]:
        """
        Activate a tool plugin by name.

        Args:
            name: Plugin name
            handler: SuperKikHandler instance
            config: Optional plugin configuration

        Returns:
            Activated plugin instance, or None if failed
        """
        if name in self._activated:
            return self._instances.get(name)

        # Get or load plugin class
        plugin_class = self._registered.get(name)
        if plugin_class is None:
            plugin_class = self._load_builtin(name)

        if plugin_class is None:
            self._logger.warning(f"Tool plugin not found: {name}")
            return None

        try:
            # Create instance
            instance = plugin_class(
                config=config or ToolPluginConfig(),
                logger=self._logger.getChild(name),
            )

            # Initialize
            await instance.initialize(handler)

            self._instances[name] = instance
            self._activated.add(name)

            tool_names = instance.get_tool_names()
            self._logger.info(f"Activated tool plugin: {name} (tools: {tool_names})")
            return instance

        except Exception as e:
            self._logger.error(f"Failed to activate tool plugin {name}: {e}")
            return None

    async def activate_from_config(
        self,
        handler: "SuperKikHandler",
        config: Dict[str, Any],
    ) -> List[str]:
        """
        Activate tool plugins based on configuration.

        Reads plugin list from config or enables defaults based on feature flags.

        Args:
            handler: SuperKikHandler instance
            config: Handler configuration dict

        Returns:
            List of successfully activated plugin names
        """
        # Get tool plugins from config
        superkik_config = config.get("superkik", {})
        if isinstance(superkik_config, str):
            superkik_config = {}

        tools_config = superkik_config.get("tool_plugins", {})

        # Default: enable all built-in plugins unless explicitly disabled
        plugin_names: List[str] = []

        # Check each built-in plugin
        for name in self._builtin_plugins:
            plugin_config = tools_config.get(name, {})

            # Skip if explicitly disabled
            if plugin_config.get("enabled") is False:
                continue

            # Check feature flags for specific plugins
            if name == "places":
                # Enable places if search is configured or not explicitly disabled
                if config.get("enable_provider_search", True):
                    plugin_names.append(name)
            elif name == "telephony":
                # Enable telephony if call patching is enabled
                if superkik_config.get("enable_call_patching", True):
                    plugin_names.append(name)
            elif name == "booking":
                # Enable booking if bookings are configured
                if superkik_config.get("enable_bookings", True):
                    plugin_names.append(name)
            elif name == "exa":
                # Enable exa if web search is enabled
                if superkik_config.get("enable_exa_search", True):
                    plugin_names.append(name)
            elif name == "calls":
                # Enable calls if CSV call processing is enabled
                if superkik_config.get("enable_calls", True):
                    plugin_names.append(name)
            else:
                # Enable by default for unknown plugins
                plugin_names.append(name)

        # Also check for explicit list
        explicit_tools = superkik_config.get("tools", [])
        if isinstance(explicit_tools, str):
            explicit_tools = [t.strip() for t in explicit_tools.split(",") if t.strip()]

        for name in explicit_tools:
            if name not in plugin_names:
                plugin_names.append(name)

        # Activate all plugins
        activated = []
        for name in plugin_names:
            plugin_config = self._build_plugin_config(name, config)
            if await self.activate(name, handler, plugin_config):
                activated.append(name)

        self._logger.info(f"Activated {len(activated)} tool plugins: {activated}")
        return activated

    def _build_plugin_config(
        self, name: str, config: Dict[str, Any]
    ) -> ToolPluginConfig:
        """Build plugin config from handler config."""
        superkik_config = config.get("superkik", {})
        if isinstance(superkik_config, str):
            superkik_config = {}

        tools_config = superkik_config.get("tool_plugins", {})
        plugin_opts = tools_config.get(name, {})

        options: Dict[str, Any] = {}

        if name == "places":
            options = {
                "default_location": superkik_config.get("default_location"),
                "default_search_radius_km": superkik_config.get(
                    "default_search_radius_km", 5.0
                ),
                "max_results": plugin_opts.get("max_results", 5),
            }
        elif name == "booking":
            options = {
                "auto_confirm": plugin_opts.get("auto_confirm", False),
            }
        elif name == "telephony":
            options = {
                "enable_sip": superkik_config.get("enable_call_patching", True),
            }
        elif name == "exa":
            options = {
                "max_results": plugin_opts.get("max_results", 5),
                "include_twitter": plugin_opts.get("include_twitter", True),
                "enable_research": plugin_opts.get("enable_research", True),
            }
        elif name == "calls":
            options = {
                "name_column": plugin_opts.get("name_column", "name"),
                "contact_column": plugin_opts.get("contact_column", "contact_number"),
                "auto_trigger": plugin_opts.get("auto_trigger", False),
            }

        return ToolPluginConfig(enabled=True, options=options)

    def get_all_tool_functions(self) -> List[Callable]:
        """
        Get all tool functions from activated plugins.

        Returns:
            List of @function_tool decorated functions
        """
        functions: List[Callable] = []
        for plugin in self._instances.values():
            if plugin.enabled:
                functions.extend(plugin.get_tool_functions())
        return functions

    def get_plugin(self, name: str) -> Optional[ToolPlugin]:
        """Get an activated plugin by name."""
        return self._instances.get(name)

    def is_activated(self, name: str) -> bool:
        """Check if a plugin is activated."""
        return name in self._activated

    def set_plugin_enabled(self, name: str, enabled: bool) -> bool:
        """
        Enable or disable a plugin at runtime.

        Args:
            name: Plugin name
            enabled: Whether to enable the plugin

        Returns:
            True if plugin was found and updated
        """
        plugin = self._instances.get(name)
        if plugin is None:
            self._logger.warning(f"Cannot set enabled: tool plugin {name} not found")
            return False

        plugin.set_enabled(enabled)
        return True

    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Collect metrics from all activated plugins."""
        metrics: Dict[str, Dict[str, Any]] = {}
        for name, plugin in self._instances.items():
            plugin_metrics = plugin.get_metrics()
            if plugin_metrics:
                metrics[name] = plugin_metrics
        return metrics

    async def cleanup_all(self) -> None:
        """Clean up all activated plugins."""
        for name, plugin in list(self._instances.items()):
            try:
                await plugin.cleanup()
                self._logger.debug(f"Cleaned up tool plugin: {name}")
            except Exception as e:
                self._logger.error(f"Error cleaning up tool plugin {name}: {e}")

        self._instances.clear()
        self._activated.clear()

    def __len__(self) -> int:
        return len(self._activated)

    def __contains__(self, name: str) -> bool:
        return name in self._activated
