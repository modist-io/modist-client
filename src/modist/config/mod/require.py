# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""Contains the require section of the mod configuration."""

from typing import List, Optional

from pydantic import Field

from ...core.context.system import OperatingSystem, ProcessorArchitecture
from .._common import BaseConfig
from .._types import SemanticSpec


class HostConfig(BaseConfig):
    """Defines the structure of the mod required host config."""

    version: Optional[SemanticSpec] = Field(
        None,
        title="Host Version",
        description="Describes the required host's version with a version selector",
    )


class RequireConfig(BaseConfig):
    """Defines the structure of the mod require config."""

    os: Optional[List[OperatingSystem]] = Field(
        None,
        title="Requires OS",
        description="Describes the supported operating systems for the mod",
    )
    arch: Optional[List[ProcessorArchitecture]] = Field(
        None,
        titles="Requires Architecture",
        description="Describes the supported architectures for the mod",
    )
    host: Optional[HostConfig] = Field(
        None,
        titles="Requires Host",
        description="Describes the supported host for the mod",
    )
