# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""Module that contains logic and factory methods for building the System context."""

import ctypes
import os
import sys
from dataclasses import dataclass, field
from enum import Enum
from getpass import getuser
from pathlib import Path
from platform import libc_ver, mac_ver, machine, system, win32_ver
from typing import Optional

from appdirs import user_cache_dir, user_config_dir, user_data_dir, user_log_dir
from semantic_version import Version

from .modist import get_name as get_app_name


class OperatingSystem(Enum):
    """Enumeration of supported operating systems for the mod configuration.

    .. note:: Although :func:`platform.system` can also return the value ``Java`` as a
        operating system (when executing Python from a Jython runtime), we do not
        consider it as a valid runtime and simply fail the casting of it to an
        ``OperatingSystem`` enumeration.

        If you truly need to know if the current runtime is being run in a Java VM,
        please refer to the :func:`~modist.context.python.get_implementation` helper
        function.
    """

    Windows = "windows"
    """Indicates a Windows (NT) system."""

    MacOS = "darwin"
    """Indicates a MacOS system."""

    Linux = "linux"
    """Indicates a Linux system."""


class ProcessorArchitecture(Enum):
    """Enumeration of discoverable processor architectures.

    **Please see source for documentation on available architectures.**

    .. important:: These architectures should rarely if ever be relied on as these are
        inheritted from Linux and are expaned on with several Windows defaults.
        This list is not verified or tested on any kind of available systems as that
        would be silly, annoying, and expensive.

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
    """Determine the current operating system.

    :return: The appropriate :class:`~OperatingSystem` instance if found
    :rtype: Optional[OperatingSystem]
    """

    try:
        return OperatingSystem(system().lower())
    except ValueError:
        return None


def get_is_64bit() -> bool:
    """Determine if the current operating system is 64bit.

    :return: True if the current operating system is 64bit, otherwise False
    :rtype: bool
    """

    # NOTE: we shouldn't rely on `platform.architecture` here as it will sometimes
    # be wrong on systems such as MacOS that bundle both 32bit and 64bit executables
    # together. Checkout the note on `platform.architecture` in Python docs (3.8+)
    return sys.maxsize > 2 ** 32


def get_os_version() -> Optional[Version]:
    """Determine the current operating system's approximate version.

    .. note:: We discover the operating system's current version through delgated calls
        to :func:`platform.win32_ver`, :func:`platform.mac_ver`, or
        :func:`platform.libc_ver` and pass the retrieved version string through
        :meth:`semantic_version.Version.coerce` to build a *usable* version data type.

    :return: The **approximate** :class:`~semantic_version.Version` instance for the
        operating system's current release version
    :rtype: Optional[~semantic_version.Version]
    """

    os_type = get_os()
    if os_type == OperatingSystem.Windows:
        _, version_string, *_ = win32_ver()
        return Version.coerce(version_string)
    elif os_type == OperatingSystem.MacOS:
        version_string, *_ = mac_ver()
        return Version.coerce(version_string)
    elif os_type == OperatingSystem.Linux:
        _, version_string = libc_ver()
        return Version.coerce(version_string)
    else:
        return None


def get_arch() -> Optional[ProcessorArchitecture]:
    """Determine the current processor architecture.

    :return: The appropriate :class:`~ProcessorArchitecture` instance if found
    :rtype: Optional[ProcessorArchitecture]
    """

    local_arch = machine().lower()
    for arch in ProcessorArchitecture:
        if local_arch.startswith(arch.value):
            return arch
    else:
        return None


def get_cwd() -> Path:
    """Determine the current working directory.

    :return: The appropriate current working directory path
    :rtype: ~pathlib.Path
    """

    return Path.cwd()


def get_is_elevated() -> bool:
    """Determine if the current user has elevated permissions.

    :return: True if the current process has elevated permissions
    :rtype: bool
    """

    os_type = get_os()
    if os_type in (OperatingSystem.MacOS, OperatingSystem.Linux,):
        # Using `geteuid` rather than `getuid` in this instance as we need the
        # "effective" (`e`) uid which is what is active in both frozen and non-frozen
        # runtimes (such as those frozen with cxFreeze or pyinstaller)
        return os.geteuid() == 0
    elif os_type == OperatingSystem.Windows:
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() == 1  # type: ignore
        except AttributeError:
            # Can sometimes occur in Windows XP as `IsUserAnAdmin` wasn't added until
            # a random patch release of Windows XP I think
            return False
    else:
        # In the case we can't determine if the current user is elevated, we should
        # assume they are not. This doesn't seem safe, but many use cases of this method
        # are to gate performance of tasks that already require elevation in order to
        # alert the user if they are not already elevated. In this case, the task that
        # requires elevated permissions will fail
        return False


def get_username() -> str:
    """Determine the current user's username.

    :return: The current user's username
    :rtype: str
    """

    return getuser()


def get_home_dir() -> Path:
    """Determine the current user's home directory.

    :return: The current user's home directory
    :rtype: ~pathlib.Path
    """

    return Path.home()


def get_config_dir() -> Path:
    """Determine the current user's config directory.

    :return: The current user's config directory
    :rtype: ~pathlib.Path
    """

    return Path(user_config_dir(get_app_name()))


def get_data_dir() -> Path:
    """Determine the current user's data directory.

    :return: The current user's data directory
    :rtype: ~pathlib.Path
    """

    return Path(user_data_dir(get_app_name()))


def get_cache_dir() -> Path:
    """Determine the current user's cache directory.

    :return: The current user's cache directory
    :rtype: ~pathlib.Path
    """

    return Path(user_cache_dir(get_app_name()))


def get_log_dir() -> Path:
    """Determine the current user's log directory.

    :return: The current user's log directory
    :rtype: ~pathlib.Path
    """

    return Path(user_log_dir(get_app_name()))


@dataclass
class UserContext:
    """Dataclass that contains the user-specific context details.

    Iniitalizing this class with no parameters will dynamically resolve the parameters
    using the included factory methods as the base :class:`~modist.context.Context`
    dataclass does.

    >>> from modist.context.system import UserContext
    >>> ctx = UserContext()
    ctx.home_dir

    :param str username: The username of the active user
    :param ~pathlib.Path home_dir: The home directory of the active user
    :param ~pathlib.Path config_dir: The client config directory for the active user
    :param ~pathlib.Path data_dir: The client data directory for the active user
    :param ~pathlib.Path cache_dir: The client cache directory for the active user
    :param ~pathlib.Path log_dir: The client log directory for the active user
    """

    username: str = field(default_factory=get_username)
    home_dir: Path = field(default_factory=get_home_dir)
    config_dir: Path = field(default_factory=get_config_dir)
    data_dir: Path = field(default_factory=get_data_dir)
    cache_dir: Path = field(default_factory=get_cache_dir)
    log_dir: Path = field(default_factory=get_log_dir)


@dataclass
class SystemContext:
    """Dataclass that contains the system-specific context details.

    Iniitalizing this class with no parameters will dynamically resolve the parameters
    using the included factory methods as the base :class:`~modist.context.Context`
    dataclass does.

    >>> from modist.context.system import SystemContext
    >>> ctx = SystemContext()
    >>> ctx.is_64bit

    :param bool is_64bit: True if the current system is 64bit
    :param bool is_elevated: True if the current runtime has elevated permissions
    :param OperatingSystem os: The current operating system
    :param Optional[~semantic_version.Version] os_version: The approximate operating
        system's semantic version
    :param Optional[ProcessorArchitecture] arch: The discovered machine architecture
    :param ~pathlib.Path cwd: The current working directory of the client
    :param UserContext user: The system's user context instance
    """

    is_64bit: bool = field(default_factory=get_is_64bit)
    is_elevated: bool = field(default_factory=get_is_elevated)
    os: Optional[OperatingSystem] = field(default_factory=get_os)
    os_version: Optional[Version] = field(default_factory=get_os_version)
    arch: Optional[ProcessorArchitecture] = field(default_factory=get_arch)
    cwd: Path = field(default_factory=get_cwd)

    user: UserContext = field(default_factory=UserContext)

    @property
    def is_windows(self) -> bool:
        """Get ``True`` if the current operating system is Windows."""

        return self.os == OperatingSystem.Windows

    @property
    def is_macos(self) -> bool:
        """Get ``True`` if the current operating system is MacOS."""

        return self.os == OperatingSystem.MacOS

    @property
    def is_linux(self) -> bool:
        """Get ``True`` if the current operating system is Linux."""

        return self.os == OperatingSystem.Linux

    @property
    def is_posix(self) -> bool:
        """Get ``True`` if the current operating system is Posix compatible."""

        return self.os in (OperatingSystem.MacOS, OperatingSystem.Linux,)
