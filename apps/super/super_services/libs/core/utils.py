import os

def get_env_name():
    env =  os.environ.get("ENV", os.environ.get("SETTINGS_FILE", "super_services.settings.qa").split(".")[-1])
    return env

