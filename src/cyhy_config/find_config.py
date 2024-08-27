"""Finds a CyHy configuration.

This module provides a function to find a CyHy configuration file.

It will search in the following locations:
 - A location passed in as a parameter
 - Environment variables
 - The current working directory
 - The user's home directory
 - The system's /etc directory
"""

# Standard Python Libraries
import logging
from os import environ
from pathlib import Path

CYHY_CONFIG_PATH = "CYHY_CONFIG_PATH"


def find_config(config_path: str = None) -> Path:
    """Find a CyHy configuration file.

    Args:
        config_path: A path to a configuration file. If provided, this
            function will return this path if it exists.

    Returns:
        The path to a CyHy configuration file.

    Raises:
        FileNotFoundError: If no configuration file is found.
    """
    # Check if the provided path exists
    if config_path and Path(config_path).exists():
        logging.debug("Using configuration file passed as parameter: %s", config_path)
        return Path(config_path)

    # Check environment variables
    env_value = environ.get(CYHY_CONFIG_PATH, None)
    if env_value:
        env_path = Path(env_value)
        if env_path.exists():
            logging.debug(
                "Using configuration file from environment variable: %s", env_path
            )
            return env_path

    # Check the current working directory
    cwd_path = Path("cyhy.toml")
    if cwd_path.exists():
        logging.debug(
            "Using configuration file from current working directory: %s", cwd_path
        )
        return cwd_path

    # Check the user's home directory
    home_path = Path.home() / ".cyhy/cyhy.toml"
    if home_path.exists():
        logging.debug("Using configuration file from home directory: %s", home_path)
        return home_path

    # Check the system's /etc directory
    etc_path = Path("/etc/cyhy.toml")
    if etc_path.exists():
        logging.debug("Using configuration file from /etc directory: %s", etc_path)
        return etc_path

    # If no configuration file is found, raise an exception
    logging.error("No CyHy configuration file found.")
    raise FileNotFoundError("No CyHy configuration file found.")
