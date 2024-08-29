"""Reads and validates a CyHy configuration file."""

# Standard Python Libraries
import logging
import os
import pprint
import tomllib
from typing import Type, TypeVar

# Third-Party Libraries
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)


# Define a TypeVar that is bound to BaseModel
T = TypeVar("T", bound=BaseModel)


def read_config(config_file: str, model: Type[T]) -> T:
    """Read the configuration file and return its contents as a dictionary."""
    pp = pprint.PrettyPrinter(indent=4)

    if not os.path.isfile(config_file):
        logger.error("Config file not found: %s", config_file)
        raise FileNotFoundError(f"Config file not found: {config_file}")

    try:
        logger.debug("Reading config file: %s", config_file)
        with open(config_file, "rb") as f:
            config_dict = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        logger.error("Error decoding toml file: %s", e)
        raise e

    try:
        config = model(**config_dict)
        logger.debug("Parsed configuration:\n%s", pp.pformat(config.model_dump()))
        return config
    except ValidationError as e:
        logger.error(e)
        raise e
