from super.core.plugin.simple import SimplePluginService


def load_class(location, config):
    system_class = SimplePluginService().get_plugin(location)
    system_parameter = system_class.__init__.__annotations__
    system_kwargs = {}
    for key in config:
        if key in system_parameter:
            system_kwargs[key] = config[key]
    if "logger" in system_parameter:
        system_kwargs["logger"] = None
    system_instance = system_class(
        **system_kwargs,
    )
    return system_instance
