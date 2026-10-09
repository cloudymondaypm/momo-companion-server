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
    Simplified configuration check; report which config file is in use
    """
    custom_config_file = get_project_dir() + "data/." + default_config_file
    if not os.path.exists(custom_config_file):
        raise FileNotFoundError(
            "Missing data/.config.yaml. Please verify that this file exists according to the setup guide."
        )

    # Check whether configuration is loaded from API
    config = asyncio.run(load_config())
    if config.get("read_config_from_api", False):
        print("Loading configuration from API")
        old_config_origin = read_config(custom_config_file)
        if old_config_origin.get("selected_module") is not None:
            error_msg = "Your configuration appears to combine management-console and local settings:\n"
            error_msg += "\nRecommended steps:\n"
            error_msg += "1. Copy config_from_api.yaml from the project root into data/ and rename it .config.yaml\n"
            error_msg += "2. Set the API endpoint and secret according to the setup guide.\n"
            raise ValueError(error_msg)
    config_file_valid = True
