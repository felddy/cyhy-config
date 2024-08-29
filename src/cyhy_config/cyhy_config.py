"""CyHy Configuration tool."""

# Standard Python Libraries
import argparse
import logging
import os
import pprint
import sys
import tomllib

# Third-Party Libraries
from pydantic import ValidationError
from rich.logging import RichHandler
from rich.traceback import install as traceback_install

from . import find_config, read_config
from ._version import __version__


def main() -> None:
    """Set up logging and call the process function."""
    parser = argparse.ArgumentParser(
        description="CyHy Configuration tool",
    )
    parser.add_argument(
        "config_file",
        help="path to the configuration file",
        metavar="config-file",
        nargs="?",
        type=str,
    )
    parser.add_argument(
        "--log-level",
        "-l",
        help="set the logging level",
        choices=["debug", "info", "warning", "error", "critical"],
        default="info",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )

    args = parser.parse_args()

    # Set up root logging
    logging.basicConfig(
        level="INFO",
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(rich_tracebacks=True, show_path=args.log_level == "debug")
        ],
    )
    # Set logging level for our package
    logger = logging.getLogger(__package__)
    logger.setLevel(args.log_level.upper())

    # Set up tracebacks
    traceback_install(show_locals=True)

    # Find the configuration file
    try:
        config_file = find_config(args.config_file)
    except FileNotFoundError:
        sys.exit(1)

    # Read the configuration file
    try:
        config = read_config(config_file)
    except ValidationError:
        sys.exit(1)

    # Stop logging and clean up
    logging.shutdown()
