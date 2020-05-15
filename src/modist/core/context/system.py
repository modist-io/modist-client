# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""
"""

import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from platform import machine, release, system
from typing import Optional


class OperatingSystem(Enum):
    """Enumeration of supported operating systems for the mod configuration."""

    Windows = "windows"
    MacOS = "darwin"
    Linux = "linux"


class ProcessorArchitecture(Enum):
    """Enumeration of discoverable processor architectures.

    .. important:: These architectures should rarely if ever be relied on as these are
        inheritted from Linux and expaned on with several Windows defaults. This list
        is not verified or tested on any kind of available systems as that would be
        annoying and expensive.

        This list was originally taken from https://stackoverflow.com/a/45125525/7828560
        and the steps provided there will give you a general understanding on why we
        can't really rely on these values always being present.
    """

    ALPHA = "alpha"
    ARC = "arc"
    ARM = "arm"
    AARCH64_BE = "aarch64_be"
    AARCH64 = "aarch64"
    ARMV8B = "armv8b"
    ARMV8L = "armv8l"
    BLACKFIN = "blackfin"
    C6X = "c6x"
    CRIS = "cris"
    FRV = "frv"
    H8300 = "h8300"
    HEXAGON = "hexagon"
    I386 = "i386"
    I686 = "i686"
    IA32 = "ia32"
    IA64 = "ia64"
    M32R = "m32r"
    M68K = "m68k"
    METAG = "metag"
    MICROBLAZE = "microblaze"
    MIPS = "mips"
    MIPS64 = "mips64"
    MN103000 = "mn103000"
    NIOS2 = "nios2"
    OPENRISC = "openrisc"
    PARISC = "parisc"
    PARISC64 = "parisc64"
    PPC = "ppc"
    PPC64 = "ppc64"
    PPCLE = "ppcle"
    PPC64LE = "ppc64le"
    S390 = "s390"
    S390X = "s390x"
    SCORE = "score"
    SH = "sh"
    SH64 = "sh64"
    SPARC = "sparc"
    SPARC64 = "sparc64"
    TILE = "tile"
    UNICORE32 = "unicore32"
    X86_32 = "x86_32"
    X86_64 = "x86_64"
    XTENSA = "xtensa"


def get_os() -> Optional[OperatingSystem]:
    try:
        return OperatingSystem(system().lower())
    except ValueError:
        return None


def get_is_64bit() -> bool:
    return sys.maxsize > 2 ** 32


def get_os_release() -> Optional[str]:
    return release()


def get_arch() -> Optional[ProcessorArchitecture]:
    local_arch = machine().lower()
    for arch in ProcessorArchitecture:
        if local_arch.startswith(arch.value):
            return arch
    else:
        return None


@dataclass
class SystemContext:

    is_64bit: bool = field(default_factory=get_is_64bit)
    os: Optional[OperatingSystem] = field(default_factory=get_os)
    os_release: Optional[str] = field(default_factory=get_os_release)
    arch: Optional[ProcessorArchitecture] = field(default_factory=get_arch)
    cwd: Path = field(default_factory=Path.cwd)
