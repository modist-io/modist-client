# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""Contains unit-tests for System context features."""

import os
from pathlib import Path, WindowsPath
from tempfile import TemporaryDirectory
from typing import List
from unittest.mock import patch

import appdirs
import pytest
from hypothesis import assume, given
from hypothesis.strategies import characters, integers, lists, sampled_from, text
from semantic_version import Version

from modist.context import modist, system

from ..conftest import cd, os_environ
from ..strategies import pathlib_path, semver_version

AVAILABLE_OPERATING_SYSTEMS = [_.value for _ in system.OperatingSystem]
AVAILABLE_PROCESSOR_ARCHITECTURES = [_.value for _ in system.ProcessorArchitecture]


@given(sampled_from(AVAILABLE_OPERATING_SYSTEMS))
def test_get_os(os_value: str):
    """Ensure call to get_os returns the correct OperatingSystem."""

    with patch.object(system, "system") as mocked_system:
        mocked_system.return_value = os_value.title()

        os_type = system.get_os()
        assert isinstance(os_type, system.OperatingSystem)
        assert os_type == system.OperatingSystem(os_value)


@given(text())
def test_get_os_returns_None(os_value: str):
    """Ensure call to get_os will return None if necessary."""

    assume(os_value not in AVAILABLE_OPERATING_SYSTEMS)

    with patch.object(system, "system") as mocked_system:
        mocked_system.return_value = os_value

        assert system.get_os() is None


def test_is_64bit():
    """Ensure call to get_is_64bit will return True on 64bit systems."""

    assert system.get_is_64bit()

    with patch.object(system, "sys") as mocked_sys:
        mocked_sys.maxsize = 2 ** 32

        assert not system.get_is_64bit()


@given(semver_version())
def test_get_os_version(version_value: str):
    """Ensure call to get_os_version responds with appropriate Version instance.

    .. note: This test is mostly mocked out of existence and is used for ensuring
        that tests are aware of future changes as context is a critical data type.
    """

    with patch.object(system, "get_os") as mocked_get_os:
        mocked_get_os.return_value = system.OperatingSystem.Windows

        with patch.object(system, "win32_ver") as mocked_win32_ver:
            mocked_win32_ver.return_value = (
                None,
                version_value,
            )

            version = system.get_os_version()
            assert isinstance(version, Version)
            assert version == Version(version_value)

    with patch.object(system, "get_os") as mocked_get_os:
        mocked_get_os.return_value = system.OperatingSystem.MacOS

        with patch.object(system, "mac_ver") as mocked_mac_ver:
            mocked_mac_ver.return_value = (version_value,)

            version = system.get_os_version()
            assert isinstance(version, Version)
            assert version == Version(version_value)

    with patch.object(system, "get_os") as mocked_get_os:
        mocked_get_os.return_value = system.OperatingSystem.Linux

        with patch.object(system, "libc_ver") as mocked_libc_ver:
            mocked_libc_ver.return_value = (
                None,
                version_value,
            )

            version = system.get_os_version()
            assert isinstance(version, Version)
            assert version == Version(version_value)


def test_get_os_version_returns_None():
    """Ensure call to get_os_version returns None when necessary."""

    with patch.object(system, "get_os") as mocked_get_os:
        mocked_get_os.return_value = None

        assert system.get_os_version() is None


@pytest.mark.skipif(
    system.get_os() != system.OperatingSystem.Windows,
    reason="os specific test only works in Windows",
)
def test_get_os_version_windows():
    """Ensure call to get_os_version works as expected on Windows."""

    with patch.object(system, "win32_ver", wraps=system.win32_ver) as mocked_win32_ver:
        assert isinstance(system.get_os_version(), Version)
        mocked_win32_ver.assert_called_once()


@pytest.mark.skipif(
    system.get_os() != system.OperatingSystem.MacOS,
    reason="os specific test only works in MacOS",
)
def test_get_os_version_mac():
    """Ensure call to get_os_version works as expected on MacOS."""

    with patch.object(system, "mac_ver", wraps=system.mac_ver) as mocked_mac_ver:
        assert isinstance(system.get_os_version(), Version)
        mocked_mac_ver.assert_called_once()


@pytest.mark.skipif(
    system.get_os() != system.OperatingSystem.Linux,
    reason="os specific test only works in Linux",
)
def test_get_os_version_linux():
    """Ensure call to get_os_version works as expected on Linux."""

    with patch.object(system, "libc_ver", wraps=system.libc_ver) as mocked_libc_ver:
        assert isinstance(system.get_os_version(), Version)
        mocked_libc_ver.assert_called_once()


@given(sampled_from(AVAILABLE_PROCESSOR_ARCHITECTURES))
def test_get_arch(arch_value: str):
    """Ensure call to get_arch returns appropriate ProcessorArchitecture instance."""

    with patch.object(system, "machine") as mocked_machine:
        mocked_machine.return_value = arch_value

        arch_type = system.get_arch()
        assert isinstance(arch_type, system.ProcessorArchitecture)
        assert arch_type == system.ProcessorArchitecture(arch_type)


@given(text())
def test_get_arch_returns_None(arch_value: str):
    """Ensure call to get_arch returns None when necessary."""

    assume(arch_value not in AVAILABLE_PROCESSOR_ARCHITECTURES)
    with patch.object(system, "machine") as mocked_machine:
        mocked_machine.return_value = arch_value

        assert system.get_arch() is None


def test_get_cwd():
    """Ensure call to get_cwd gets the appropriate current working directory."""

    cwd = system.get_cwd()
    assert isinstance(cwd, Path)
    assert cwd == Path.cwd()

    with TemporaryDirectory() as temp_dirname:
        temp_dirpath = Path(temp_dirname).resolve()
        with cd(temp_dirpath):
            cwd = system.get_cwd()
            assert isinstance(cwd, Path)
            assert cwd == temp_dirpath


def test_get_is_elevated():
    """Ensure call to get_is_elevated works as expected.

    .. note:: This test is mostly mocked out of existence and is being used to ensure
        that tests are aware of future changes as context is a critical data type.
    """

    # posix style full-mock tests
    for posix_os_type in (
        system.OperatingSystem.MacOS,
        system.OperatingSystem.Linux,
    ):
        with patch.object(system, "get_os") as mocked_get_os:
            mocked_get_os.return_value = posix_os_type

            with patch.object(system, "os") as mocked_os:
                mocked_os.geteuid.return_value = 0
                assert system.get_is_elevated()

                mocked_os.geteuid.reset_mock()
                mocked_os.geteuid.return_value = 1
                assert not system.get_is_elevated()

    # windows-specific full-mock tests
    with patch.object(system, "get_os") as mocked_get_os:
        mocked_get_os.return_value = system.OperatingSystem.Windows

        with patch.object(system, "ctypes") as mocked_ctypes:
            mocked_ctypes.windll.shell32.IsUserAnAdmin.side_effect = AttributeError
            assert not system.get_is_elevated()

        with patch.object(system, "ctypes") as mocked_ctypes:
            mocked_ctypes.windll.shell32.IsUserAnAdmin.return_value = 1
            assert system.get_is_elevated()

            mocked_ctypes.windll.shell32.IsUserAnAdmin.reset_mock()
            mocked_ctypes.windll.shell32.IsUserAnAdmin.return_value = 0
            assert not system.get_is_elevated()


def test_get_is_elevated_with_invalid_os():
    """Ensure that call to get_is_elevated returns None with an invalid os."""

    with patch.object(system, "get_os") as mocked_get_os:
        mocked_get_os.return_value = None

        assert not system.get_is_elevated()


@pytest.mark.skipif(
    system.get_os()
    not in (system.OperatingSystem.MacOS, system.OperatingSystem.Linux,),
    reason="os specific test only works in MacOS or Linux",
)
def test_get_is_elevated_posix():
    """Ensure call to get_is_elevated works as expected on Posix systems."""

    with patch.object(system.os, "geteuid", wraps=system.os.geteuid) as mocked_geteuid:
        assert not system.get_is_elevated()
        mocked_geteuid.assert_called_once()

    with patch.object(system.os, "geteuid") as mocked_geteuid:
        mocked_geteuid.return_value = 0
        assert system.get_is_elevated()


@pytest.mark.skipif(
    system.get_os() != system.OperatingSystem.Windows,
    reason="os specific test only works in Windows",
)
def test_get_is_elevated_windows():
    """Ensure call to get_is_elevated works as expected on Windows."""

    with patch.object(system, "ctypes", wraps=system.ctypes) as mocked_ctypes:
        if os.environ.get("CI", False):
            # NOTE: Github CI tests run with administrator priveledges
            assert system.get_is_elevated()
        else:
            assert not system.get_is_elevated()
        system.ctypes.windll.shell32.IsUserAnAdmin.assert_called_once()

    with patch.object(system, "ctypes") as mocked_ctypes:
        mocked_ctypes.windll.shell32.IsUserAnAdmin.return_value = 1
        assert system.get_is_elevated()


@given(lists(integers()), integers(min_value=0))
def test_get_available_cpu_count(cpu_affinity: List[int], cpu_count: int):
    """Ensure call to get_available_cpu_count works as expected."""

    for affinity_os_type in (
        system.OperatingSystem.Linux,
        system.OperatingSystem.Windows,
    ):
        with patch.object(system, "get_os") as mocked_get_os:
            mocked_get_os.return_value = affinity_os_type

            with patch.object(system.psutil, "Process") as mocked_Process:
                mocked_Process().cpu_affinity.return_value = cpu_affinity

                assert system.get_available_cpu_count() == len(cpu_affinity)

    with patch.object(system, "get_os") as mocked_get_os:
        mocked_get_os.return_value = system.OperatingSystem.MacOS

        with patch.object(system.psutil, "cpu_count") as mocked_cpu_count:
            mocked_cpu_count.return_value = cpu_count

            assert system.get_available_cpu_count() == cpu_count


@pytest.mark.skipif(
    system.get_os()
    not in (system.OperatingSystem.Linux, system.OperatingSystem.Windows,),
    reason="os specific test only works in Linux or Windows",
)
@given(lists(integers()))
def test_get_available_cpu_count_non_mac(cpu_affinity: List[int]):
    """Ensure call to get_available_cpu_count works as expected on non MacOS systems."""

    assert system.get_available_cpu_count() > 0

    with patch.object(system.psutil, "Process") as mocked_Process:
        mocked_cpu_affinity = mocked_Process().cpu_affinity
        mocked_cpu_affinity.return_value = cpu_affinity

        assert system.get_available_cpu_count() == len(cpu_affinity)
        mocked_cpu_affinity.assert_called_once()


@pytest.mark.skipif(
    system.get_os() != system.OperatingSystem.MacOS,
    reason="os specific test only works in MacOS",
)
@given(integers(min_value=0))
def test_get_available_cpu_count_mac(cpu_count: int):
    """Ensure call to get_available_cpu_count works as expected on MacOS systems."""

    assert system.get_available_cpu_count() > 0
    with patch.object(system.psutil, "cpu_count") as mocked_cpu_count:
        mocked_cpu_count.return_value = cpu_count

        assert system.get_available_cpu_count() == cpu_count
        mocked_cpu_count.assert_called_once()


@given(text(alphabet=characters(blacklist_categories=["C", "Z"])))
def test_get_username(username: str):
    """Ensure call to get_username works as expected."""

    with patch.object(system, "getuser") as mocked_getuser:
        mocked_getuser.return_value = username

        assert system.get_username() == username


@pytest.mark.skipif(
    system.get_os() == system.OperatingSystem.Windows,
    reason="os specific test only works in Posix compatible systems",
)
@given(pathlib_path())
def test_get_home_dir_posix(path: Path):
    """Ensure call to get_home_dir works as expected in Posix compatible systems."""

    assert isinstance(system.get_home_dir(), Path)
    with os_environ({"HOME": path.as_posix()}):
        assert system.get_home_dir() == path


@pytest.mark.skipif(
    system.get_os() != system.OperatingSystem.Windows,
    reason="os specific test only works in Windows",
)
def test_get_home_dir_windows():
    """Ensure call to get_home_dir works as expected in Windows."""

    # NOTE: WindowsPath does not obey the $HOME environment variable, so testing with
    # changing $HOME will not work. The best we can do here is ensure that the found
    # path is a WindowsPath rathern than just a regular ol' Path or PurePath
    assert isinstance(system.get_home_dir(), WindowsPath)


def test_get_config_dir():
    """Ensure call to get_config_dir works as expected for the current user."""

    config_dir = system.get_config_dir()
    assert isinstance(config_dir, Path)
    assert config_dir == Path(appdirs.user_config_dir(modist.get_name()))


def test_get_data_dir():
    """Ensure call to get_data_dir works as expected for the current user."""

    data_dir = system.get_data_dir()
    assert isinstance(data_dir, Path)
    assert data_dir == Path(appdirs.user_data_dir(modist.get_name()))


def test_get_cache_dir():
    """Ensure call to get_cache_dir works as expected for the current user."""

    cache_dir = system.get_cache_dir()
    assert isinstance(cache_dir, Path)
    assert cache_dir == Path(appdirs.user_cache_dir(modist.get_name()))


def test_get_log_dir():
    """Ensure call to get_log_dir works as expected for the current user."""

    log_dir = system.get_log_dir()
    assert isinstance(log_dir, Path)
    assert log_dir == Path(appdirs.user_log_dir(modist.get_name()))


def test_UserContext_default():
    """Ensure the construction of UserContext doesn't do any unexpected mutation."""

    ctx = system.UserContext()

    assert ctx.username == system.get_username()
    assert ctx.home_dir == system.get_home_dir()
    assert ctx.config_dir == system.get_config_dir()
    assert ctx.data_dir == system.get_data_dir()
    assert ctx.cache_dir == system.get_cache_dir()
    assert ctx.log_dir == system.get_log_dir()


def test_SystemContext_default():
    """Ensure the construction of SystemContext doesn't do any unexpected mutation."""

    ctx = system.SystemContext()

    assert ctx.is_64bit == system.get_is_64bit()
    assert ctx.is_elevated == system.get_is_elevated()
    assert ctx.available_cpu_count == system.get_available_cpu_count()
    assert ctx.os == system.get_os()
    assert ctx.os_version == system.get_os_version()
    assert ctx.arch == system.get_arch()
    assert ctx.cwd == system.get_cwd()

    assert ctx.user == system.UserContext()


@pytest.mark.skipif(
    system.get_os() != system.OperatingSystem.Windows,
    reason="os specific test only works in Windows",
)
def test_SystemContext_is_windows():
    """Ensure the SystemContext is_windows property works properly."""

    ctx = system.SystemContext()
    assert ctx.is_windows
    assert not ctx.is_macos
    assert not ctx.is_linux
    assert not ctx.is_posix


@pytest.mark.skipif(
    system.get_os() != system.OperatingSystem.MacOS,
    reason="os specific test only works in MacOS",
)
def test_SystemContext_is_macos():
    """Ensure the SystemContext is_macos property works properly."""

    ctx = system.SystemContext()
    assert not ctx.is_windows
    assert ctx.is_macos
    assert not ctx.is_linux
    assert ctx.is_posix


@pytest.mark.skipif(
    system.get_os() != system.OperatingSystem.Linux,
    reason="os specific test only works in Linux",
)
def test_SystemContext_is_linux():
    """Ensure the SystemContext is_linux property works properly."""

    ctx = system.SystemContext()
    assert not ctx.is_windows
    assert not ctx.is_macos
    assert ctx.is_linux
    assert ctx.is_posix
