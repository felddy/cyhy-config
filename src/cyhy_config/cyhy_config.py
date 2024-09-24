"""Finds a CyHy configuration.

This module provides a function to find a CyHy configuration file.

It will search in the following locations:
 - A location passed in as a parameter
 - Environment variables for an SSM parameter path
 - Environment variables for a file path
 - The current working directory
 - The user's home directory
 - The system's /etc directory
"""

# Standard Python Libraries
import logging
import os
from os import environ
from pathlib import Path
import pprint
import tomllib
from typing import Optional, Type, TypeVar

# Third-Party Libraries
from boto3 import client
from botocore.exceptions import ClientError
from pydantic import BaseModel, ValidationError

CYHY_CONFIG_PATH = "CYHY_CONFIG_PATH"
CYHY_CONFIG_SSM_PATH = "CYHY_CONFIG_SSM_PATH"

# Ensure the logger is under the common CyHy namespace
logger = logging.getLogger(f"cyhy.{__name__}")
pp = pprint.PrettyPrinter(indent=4)

# Define a TypeVar that is bound to BaseModel
T = TypeVar("T", bound=BaseModel)


def get_config(
    file_path: Optional[str] = None,
    ssm_path: Optional[str] = None,
    model: Optional[Type[T]] = None,
) -> T | dict:
    """Get the CyHy configuration."""
    # First we try to find the configuration file in SSM
    # If we can't find it there, we look for it in a file
    config = read_config_ssm(ssm_path, model)
    if config:
        return config

    # We didn't find the configuration in SSM, so we look for it in a file
    config_file_path = find_config_file(file_path)

    return read_config_file(config_file_path, model)


def find_config_file(file_path: Optional[str] = None) -> Path:
    """Find a CyHy configuration file.

    Args:
        file_path: A path to a configuration file.

    Returns:
        A path to a CyHy configuration file.

    Raises:
        FileNotFoundError: If no configuration file is found.
    """
    # Check if the provided path exists
    if file_path:
        if Path(file_path).exists():
            logger.debug("Using configuration file passed as parameter: %s", file_path)
            return Path(file_path)
        else:
            logger.warning(
                "Configuration file passed as parameter not found: %s", file_path
            )

    # Check environment variable for file path
    env_file_value = environ.get(CYHY_CONFIG_PATH, None)
    if env_file_value:
        env_path = Path(env_file_value)
        if env_path.exists():
            logger.debug(
                "Using configuration file from environment variable: %s", env_path
            )
            return env_path
        else:
            logger.warning(
                "Configuration file from environment variable not found: %s", env_path
            )

    # Check the current working directory
    cwd_path = Path("cyhy.toml")
    if cwd_path.exists():
        logger.debug(
            "Using configuration file from current working directory: %s", cwd_path
        )
        return cwd_path

    # Check the user's home directory
    home_path = Path.home() / ".cyhy/cyhy.toml"
    if home_path.exists():
        logger.debug("Using configuration file from home directory: %s", home_path)
        return home_path

    # Check the system's /etc directory
    etc_path = Path("/etc/cyhy.toml")
    if etc_path.exists():
        logger.debug("Using configuration file from /etc directory: %s", etc_path)
        return etc_path

    # If no configuration file is found, raise an exception
    logger.error("No CyHy configuration file found.")
    raise FileNotFoundError("No CyHy configuration file found.")


def read_config_ssm(
    ssm_path: Optional[str] = None, model: Optional[Type[T]] = None
) -> T | dict | None:
    """Read the configuration from SSM and return its contents as a dictionary."""
    ssm_paths = [
        (ssm_path, "path"),
        (environ.get(CYHY_CONFIG_SSM_PATH, None), "environment variable"),
    ]

    for path, source in ssm_paths:
        logger.debug("Checking SSM parameter from %s: %s", source, path)
        if path:
            ssm = client("ssm")
            try:
                response = ssm.get_parameter(Name=path, WithDecryption=True)
            except ClientError as e:
                if e.response["Error"]["Code"] == "ParameterNotFound":
                    logger.warning("SSM parameter not found: %s", path)
                    return None
                else:
                    logger.error(e)
                    raise e

            param_value = response["Parameter"]["Value"]
            logger.debug("Using configuration file from SSM %s: %s", source, path)
            try:
                config_dict = tomllib.loads(param_value)
            except tomllib.TOMLDecodeError as e:
                logger.error("Error decoding TOML: %s", param_value)
                raise e

            return validate_config(config_dict, model)

    return None


def read_config_file(config_file: Path, model: Optional[Type[T]] = None) -> T | dict:
    """Read the configuration file and return its contents as a dictionary."""
    if not os.path.isfile(config_file):
        logger.error("Config file not found: %s", config_file)
        raise FileNotFoundError(f"Config file not found: {config_file}")

    try:
        logger.debug("Reading config file: %s", config_file)
        with open(config_file, "rb") as f:
            config_dict = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        logger.error("Error decoding TOML file: %s", config_file)
        raise e

    return validate_config(config_dict, model)


def validate_config(config_dict: dict, model: Optional[Type[T]]) -> T | dict:
    """Validate the configuration against the model."""
    if not model:
        logger.info("No model provided, returning config as a dictionary.")
        logger.debug("Parsed configuration:\n%s", pp.pformat(config_dict))
        return config_dict
    try:
        config = model(**config_dict)
        logger.debug("Validated configuration:\n%s", pp.pformat(config.model_dump()))
        return config
    except ValidationError as e:
        logger.error(e)
        raise e
