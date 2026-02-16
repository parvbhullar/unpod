"""
Plugin registry for managing voice pipeline plugins.
"""

from typing import TYPE_CHECKING, Dict, List, Optional, Set, Type
import logging
import os

from super.core.voice.plugins.base import PipelinePlugin, PluginConfig

if TYPE_CHECKING:
    from super.core.voice.pipecat.lite_handler import LiteVoiceHandler


class PluginRegistry:
    """
    Manages registration and lifecycle of pipeline plugins.

    Plugins are registered by name and activated on-demand. The registry
    handles initialization ordering and provides processors for pipeline
    construction.

    Example:
        registry = PluginRegistry()
        registry.register(RAGPlugin)
        registry.register(TranscriptPlugin)

        await registry.activate_from_config(handler, config)
        processors = registry.get_all_processors()
    """

    # Built-in plugin classes (lazy imports to avoid circular deps)
    _builtin_plugins: Dict[str, str] = {
        "rag": "super.core.voice.plugins.rag_plugin.RAGPlugin",
        "transcript": "super.core.voice.plugins.transcript_plugin.TranscriptPlugin",
        "streaming": "super.core.voice.plugins.streaming_plugin.StreamingParserPlugin",
        "silence": "super.core.voice.plugins.silence_plugin.SilenceTrimmerPlugin",
        "idle": "super.core.voice.plugins.idle_plugin.IdleDetectorPlugin",
        "filler": "super.core.voice.plugins.filler_plugin.FillerResponsePlugin",
    }

    def __init__(self, logger: Optional[logging.Logger] = None):
        self._logger = logger or logging.getLogger("plugin.registry")
        self._registered: Dict[str, Type[PipelinePlugin]] = {}
        self._instances: Dict[str, PipelinePlugin] = {}
        self._activated: Set[str] = set()

    def register(
        self,
        plugin_class: Type[PipelinePlugin],
        name: Optional[str] = None,
    ) -> None:
        """
        Register a plugin class.

        Args:
            plugin_class: The plugin class to register
            name: Optional name override (defaults to plugin_class.name)
        """
        plugin_name = name or plugin_class.name
        self._registered[plugin_name] = plugin_class
        self._logger.debug(f"Registered plugin: {plugin_name}")

    def _load_builtin(self, name: str) -> Optional[Type[PipelinePlugin]]:
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
            self._logger.warning(f"Failed to load builtin plugin {name}: {e}")
            return None

    async def activate(
        self,
        name: str,
        handler: "LiteVoiceHandler",
        config: Optional[PluginConfig] = None,
    ) -> Optional[PipelinePlugin]:
        """
        Activate a plugin by name.

        Args:
            name: Plugin name
            handler: LiteVoiceHandler instance
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
            self._logger.warning(f"Plugin not found: {name}")
            return None

        try:
            # Create instance
            instance = plugin_class(
                config=config or PluginConfig(),
                logger=self._logger.getChild(name),
            )

            # Initialize
            await instance.initialize(handler)

            self._instances[name] = instance
            self._activated.add(name)
            self._logger.info(f"Activated plugin: {name} (priority={instance.priority})")
            return instance

        except Exception as e:
            self._logger.error(f"Failed to activate plugin {name}: {e}")
            return None

    async def activate_from_config(
        self,
        handler: "LiteVoiceHandler",
        config: dict,
    ) -> List[str]:
        """
        Activate plugins based on configuration.

        Reads plugin list from config or environment variable.

        Args:
            handler: LiteVoiceHandler instance
            config: Handler configuration dict

        Returns:
            List of successfully activated plugin names
        """
        # Get plugin list from config or env
        plugins_str = config.get(
            "plugins",
            os.getenv("LITE_PLUGINS", "transcript"),
        )

        if isinstance(plugins_str, str):
            plugin_names = [p.strip() for p in plugins_str.split(",") if p.strip()]
        else:
            plugin_names = list(plugins_str) if plugins_str else []

        # Check for feature flags that enable specific plugins
        if config.get("use_rag_processor") or config.get("knowledge_base"):
            if "rag" not in plugin_names:
                plugin_names.append("rag")

        if config.get("use_streaming_parser", True):
            if "streaming" not in plugin_names:
                plugin_names.append("streaming")

        if config.get("use_silence_trimmer"):
            if "silence" not in plugin_names:
                plugin_names.append("silence")

        # Filler can be enabled via config or env var
        filler_enabled = config.get("use_filler_response") or os.getenv(
            "FILLER_ENABLED", ""
        ).lower() == "true"
        if filler_enabled:
            if "filler" not in plugin_names:
                plugin_names.append("filler")

        activated = []
        for name in plugin_names:
            # Build plugin-specific config from handler config
            plugin_config = self._build_plugin_config(name, config)

            if await self.activate(name, handler, plugin_config):
                activated.append(name)

        self._logger.info(f"Activated {len(activated)} plugins: {activated}")
        return activated

    def _build_plugin_config(self, name: str, config: dict) -> PluginConfig:
        """Build plugin config from handler config."""
        options = {}

        if name == "rag":
            options = {
                "similarity_top_k": config.get("rag_similarity_top_k", 3),
                "kb_timeout": config.get("kb_timeout", 5.0),
            }
        elif name == "streaming":
            options = {
                "streamable_fields": config.get(
                    "streaming_parser_fields",
                    ["spoke_response", "response", "text", "answer", "content"],
                ),
                "min_chunk_size": config.get("streaming_parser_min_chunk", 1),
            }
        elif name == "silence":
            options = {
                "threshold_db": config.get("silence_threshold_db", -50.0),
                "sample_rate": config.get("tts_sample_rate", 24000),
            }
        elif name == "idle":
            options = {
                "timeout": config.get("idle_timeout", 30.0),
            }
        elif name == "filler":
            options = {
                "model": config.get("filler_model", "gpt-4o-mini"),
                "max_tokens": config.get("filler_max_tokens", 10),
                "temperature": config.get("filler_temperature", 0.7),
                "timeout": config.get("filler_timeout", 0.5),
                "skip_patterns": config.get("filler_skip_patterns", []),
            }

        return PluginConfig(enabled=True, options=options)

    def get_all_processors(self) -> List:
        """
        Get all processors from activated plugins, sorted by priority.

        Returns:
            List of processors in priority order
        """
        plugins_by_priority = sorted(
            self._instances.values(),
            key=lambda p: p.priority,
        )

        processors = []
        for plugin in plugins_by_priority:
            if plugin.enabled:
                processors.extend(plugin.get_processors())

        return processors

    def get_processors_at_priority(self, priority: int) -> List:
        """
        Get processors at a specific priority level.

        Args:
            priority: Priority level to filter by

        Returns:
            List of processors at that priority
        """
        processors = []
        for plugin in self._instances.values():
            if plugin.enabled and plugin.priority == priority:
                processors.extend(plugin.get_processors())
        return processors

    def get_plugin(self, name: str) -> Optional[PipelinePlugin]:
        """Get an activated plugin by name."""
        return self._instances.get(name)

    def is_activated(self, name: str) -> bool:
        """Check if a plugin is activated."""
        return name in self._activated

    def set_plugin_enabled(self, name: str, enabled: bool) -> bool:
        """Enable or disable a plugin at runtime.

        Args:
            name: Plugin name
            enabled: Whether to enable the plugin

        Returns:
            True if plugin was found and updated, False otherwise
        """
        plugin = self._instances.get(name)
        if plugin is None:
            self._logger.warning(f"Cannot set enabled: plugin {name} not found")
            return False

        plugin.set_enabled(enabled)
        return True

    def enable_plugin(self, name: str) -> bool:
        """Enable a plugin at runtime."""
        return self.set_plugin_enabled(name, True)

    def disable_plugin(self, name: str) -> bool:
        """Disable a plugin at runtime."""
        return self.set_plugin_enabled(name, False)

    async def broadcast_event(self, event: str, *args, **kwargs) -> None:
        """
        Broadcast an event to all activated plugins.

        Args:
            event: Event method name (e.g., "on_call_start")
            *args, **kwargs: Arguments to pass to event handler
        """
        for plugin in self._instances.values():
            if plugin.enabled and hasattr(plugin, event):
                try:
                    handler = getattr(plugin, event)
                    await handler(*args, **kwargs)
                except Exception as e:
                    self._logger.error(f"Plugin {plugin.name} error in {event}: {e}")

    def get_all_metrics(self) -> Dict[str, dict]:
        """
        Collect metrics from all activated plugins.

        Returns:
            Dict mapping plugin names to their metrics
        """
        metrics = {}
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
                self._logger.debug(f"Cleaned up plugin: {name}")
            except Exception as e:
                self._logger.error(f"Error cleaning up plugin {name}: {e}")

        self._instances.clear()
        self._activated.clear()

    def __len__(self) -> int:
        return len(self._activated)

    def __contains__(self, name: str) -> bool:
        return name in self._activated
