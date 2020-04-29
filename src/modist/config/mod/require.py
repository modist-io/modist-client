# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""Contains the require section of the mod configuration."""

from enum import Enum
from typing import List, Optional

from pydantic import Field, BaseModel


class OperatingSystem(Enum):
    """Enumeration of supported operating systems for the mod configuration."""

    WINDOWS = "windows"
    MACOS = "macos"
    LINUX = "linux"


class RequireConfig(BaseModel):
    """Defines the structure of the mod require config."""

    os: Optional[List[OperatingSystem]] = Field(
        None,
        title="Requires OS",
        description="Describes the supported operating systems for the mod",
    )
