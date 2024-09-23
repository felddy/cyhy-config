#!/usr/bin/env pytest -vs
"""Tests for cyhy_config."""

# Standard Python Libraries
import os
from pathlib import Path
import tomllib
from unittest.mock import MagicMock, mock_open, patch

# Third-Party Libraries
from botocore.exceptions import ClientError
from pydantic import BaseModel, ValidationError
import pytest

# cisagov Libraries
from cyhy_config.cyhy_config import (
    find_config_file,
    get_config,
    read_config_file,
    read_config_ssm,
    validate_config,
)


class MockModel(BaseModel):
    """Mock model for testing."""

    key: str


def test_find_config_file():
    """
    Test the find_config_file function.

    This function tests the behavior of the find_config_file function under
    different scenarios.

    Scenarios:
    1. When the given path exists, it should return the path.
    2. When the CYHY_CONFIG_PATH environment variable is set, it should return
    the path specified in the environment variable.
    3. When the cyhy.toml file exists in the current directory, it should return
    the path to the file.
    4. When the cyhy.toml file exists in the user's home directory, it should
    return the path to the file.
    5. When the cyhy.toml file exists in the /etc directory, it should return
    the path to the file.
    6. When no valid path is found, it should raise a FileNotFoundError.
    """
    with patch("cyhy_config.cyhy_config.Path.exists", return_value=True):
        assert find_config_file("/mock/path") == Path("/mock/path")

    with patch.dict(os.environ, {"CYHY_CONFIG_PATH": "/mock/env/path"}):
        with patch("cyhy_config.cyhy_config.Path.exists", return_value=True):
            assert find_config_file() == Path("/mock/env/path")

    with patch("cyhy_config.cyhy_config.Path.exists", side_effect=[True]):
        assert find_config_file() == Path("cyhy.toml")

    with patch("cyhy_config.cyhy_config.Path.exists", side_effect=[False, True]):
        assert find_config_file() == Path.home() / ".cyhy/cyhy.toml"

    with patch("cyhy_config.cyhy_config.Path.exists", side_effect=[False, False, True]):
        assert find_config_file() == Path("/etc/cyhy.toml")

    with patch("cyhy_config.cyhy_config.Path.exists", return_value=False):
        with pytest.raises(FileNotFoundError):
            find_config_file()


def test_read_config_ssm():
    """
    Test the read_config_ssm function.

    This function tests the behavior of the read_config_ssm function under
    different scenarios.

    Scenarios:
    1. When the CYHY_CONFIG_SSM_PATH environment variable is set, it should
    retrieve the parameter value from AWS SSM and return the config.
    2. When the parameter is not found in AWS SSM, it should return None.
    """
    mock_ssm_client = MagicMock()
    mock_ssm_client.get_parameter.return_value = {
        "Parameter": {"Value": 'key = "value"'}
    }

    with patch("cyhy_config.cyhy_config.client", return_value=mock_ssm_client):
        with patch.dict(os.environ, {"CYHY_CONFIG_SSM_PATH": "/mock/ssm/path"}):
            config = read_config_ssm(model=MockModel)
            assert config.key == "value"

    mock_ssm_client.get_parameter.side_effect = ClientError(
        {"Error": {"Code": "ParameterNotFound"}}, "get_parameter"
    )
    with patch("cyhy_config.cyhy_config.client", return_value=mock_ssm_client):
        assert read_config_ssm() is None


def test_read_config_file():
    """
    Test the read_config_file function.

    This function tests the behavior of the read_config_file function under
    different scenarios.

    Scenarios:
    1. When the file exists, it should read the file, parse the TOML data, and
    return the config.
    2. When the file does not exist, it should raise a FileNotFoundError.
    3. When the TOML data is invalid, it should raise a TOMLDecodeError.
    """
    mock_file_data = b'key = "value"'
    with patch("os.path.isfile", return_value=True):
        with patch("builtins.open", mock_open(read_data=mock_file_data)):
            with patch(
                "cyhy_config.cyhy_config.tomllib.load", return_value={"key": "value"}
            ):
                config = read_config_file(Path("/mock/path"), model=MockModel)
                assert config.key == "value"

    with patch("os.path.isfile", return_value=True):
        with patch("builtins.open", mock_open(read_data=mock_file_data)):
            with patch(
                "cyhy_config.cyhy_config.tomllib.load",
                side_effect=tomllib.TOMLDecodeError("Error", "doc", 0),
            ):
                with pytest.raises(tomllib.TOMLDecodeError):
                    read_config_file(Path("/mock/path"))


def test_validate_config():
    """
    Test the validate_config function.

    This function tests the behavior of the validate_config function under
    different scenarios.

    Scenarios:
    1. When the config dictionary is valid, it should return the validated config.
    2. When the config dictionary is empty, it should raise a ValidationError.
    3. When the model is None, it should return the config dictionary as is.
    """
    config_dict = {"key": "value"}
    config = validate_config(config_dict, MockModel)
    assert config.key == "value"

    with pytest.raises(ValidationError):
        validate_config({}, MockModel)

    config = validate_config(config_dict, None)
    assert config == config_dict


def test_get_config():
    """
    Test the get_config function.

    This function tests the behavior of the get_config function under different
    scenarios.

    Scenarios:
    1. When the config is retrieved from AWS SSM, it should return the config.
    2. When the config is not found in AWS SSM, it should try to find the config
    file and return the config.
    """
    with patch(
        "cyhy_config.cyhy_config.read_config_ssm", return_value={"key": "value"}
    ):
        config = get_config(model=MockModel)
        assert config["key"] == "value"

    with patch("cyhy_config.cyhy_config.read_config_ssm", return_value=None):
        with patch(
            "cyhy_config.cyhy_config.find_config_file", return_value=Path("/mock/path")
        ):
            with patch(
                "cyhy_config.cyhy_config.read_config_file",
                return_value={"key": "value"},
            ):
                config = get_config(model=MockModel)
                assert config["key"] == "value"
