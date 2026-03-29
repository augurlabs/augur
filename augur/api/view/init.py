import os
from pathlib import Path
from .server import Environment
from augur.application.logs import AugurLogger
import secrets, yaml

env = Environment()

# load configuration files and initialize globals
configFile = Path(env.setdefault("CONFIG_LOCATION", "config.yml"))

settings = {}

def init_settings():
    global settings
    settings["approot"] = "/"
    settings["caching"] = "static/cache/"
    settings["cache_expiry"] = 604800
    settings["serving"] = "http://augur.chaoss.io/api/unstable"
    settings["pagination_offset"] = 25
    settings["session_key"] = secrets.token_hex()

def write_settings(current_settings):
    current_settings["caching"] = str(current_settings["caching"])

    if "valid" in current_settings:
        current_settings.pop("valid")

    with open(configFile, 'w') as file:
        yaml.dump(current_settings, file)


# Initialize logging
def init_logging():
    global logger
    logger = AugurLogger("augur_view", reset_logfiles=False).get_logger()
