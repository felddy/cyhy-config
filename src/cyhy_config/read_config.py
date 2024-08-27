"""Reads and validates a CyHy configuration file."""

# Standard Python Libraries
import logging
import os
import pprint
import tomllib

# Third-Party Libraries
from pydantic import ValidationError

from . import CyHyConfig


def read_config(config_file: str) -> CyHyConfig:
    """Read the configuration file and return its contents as a dictionary."""
    pp = pprint.PrettyPrinter(indent=4)

    if not os.path.isfile(config_file):
        logging.error("Config file not found: %s", config_file)
        raise FileNotFoundError(f"Config file not found: {config_file}")

    try:
        logging.debug("Reading config file: %s", config_file)
        with open(config_file, "rb") as f:
            config_dict = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        logging.error("Error decoding toml file: %s", e)
        raise e

    try:
        config = CyHyConfig(**config_dict)
        logging.debug("Parsed configuration:\n%s", pp.pformat(config.model_dump()))
        return config
    except ValidationError as e:
        logging.error(e)
        raise e
