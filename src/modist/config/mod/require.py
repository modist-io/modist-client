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


class ProcessorArchitecture(Enum):
    """Enumeration of discoverable processor architectures."""

    ARM = "arm"
    ARM64 = "arm64"
    IA32 = "ia32"
    PPC = "ppc"
    PPC64 = "ppc64"
    S390 = "s390"
    S390X = "s390x"
    X32 = "x32"
    X64 = "x64"


class RequireConfig(BaseModel):
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
