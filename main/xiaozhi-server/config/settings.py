import os
import asyncio
from config.config_loader import read_config, get_project_dir, load_config


default_config_file = "config.yaml"
config_file_valid = False


def check_config_file():
    global config_file_valid
    if config_file_valid:
        return
    """
    Simple configuration check to explain how the configuration file is used
    """
    custom_config_file = get_project_dir() + "data/." + default_config_file
    if not os.path.exists(custom_config_file):
        raise FileNotFoundError(
            "Cannot find data/.config.yaml. Confirm the configuration file exists as described in the setup guide."
        )

    # Check whether configuration is loaded from the API
    config = asyncio.run(load_config())
    if config.get("read_config_from_api", False):
        print("Loading configuration from the API")
        old_config_origin = read_config(custom_config_file)
        if old_config_origin.get("selected_module") is not None:
            error_msg = "Your config file contains settings for both the management console and local configuration:\n"
            error_msg += "\nRecommended action:\n"
            error_msg += "1. Copy config_from_api.yaml from the project root to data/.config.yaml\n"
            error_msg += "2. Configure the API URL and secret according to the setup guide\n"
            raise ValueError(error_msg)
    config_file_valid = True
