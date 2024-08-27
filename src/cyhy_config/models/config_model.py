"""Model definitions for the configuration."""

# Standard Python Libraries
from pathlib import Path
import re
from typing import Any, Dict, List

# Third-Party Libraries
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Database(BaseModel):
    """Definition of an Database configuration."""

    model_config = ConfigDict(extra="forbid")

    auth_uri: str
    name: str


class Mode(BaseModel):
    """Definition of a Mode configuration."""

    model_config = ConfigDict(extra="forbid")

    database: Database
    description: str
    name: str


class CyHyConfig(BaseModel):
    """Definition of the configuration root."""

    model_config = ConfigDict(extra="forbid")

    modes: Dict[str, Mode]
    databases: Dict[str, Database]

    @model_validator(mode="before")
    def resolve_actions(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve named references."""
        # Extract databases from the values dictionary
        database_dict = values.get("databases", {})

        # Resolve the Database references in each Mode
        for mode in values.get("modes", {}).values():
            mode["database"] = database_dict[mode["database"]]
        return values
