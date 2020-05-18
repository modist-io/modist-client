# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""Contains unit-tests for the core mod functionality."""

import os
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Type
from unittest.mock import patch

import pytest
from hypothesis import assume, given

from modist.config.mod.mod import ModConfig
from modist.context import instance as ctx
from modist.core.mod import MOD_CONFIG_NAME, MOD_DIRECTORY_MODE, MOD_DIRECTORY_NAME, Mod
from modist.exceptions import IsAMod, NotAMod

from ..config.mod.strategies import minimal_mod_config_payload
from ..strategies import builtin_exceptions, pathlib_path


@given(pathlib_path())
def test_Mod_build_mod_directory_path(path: Path):
    """Ensure Mod builds the correct mod directory path given a base directory."""

    built_path = Mod.build_mod_directory_path(path)
    assert built_path.name == MOD_DIRECTORY_NAME
    assert built_path == path / MOD_DIRECTORY_NAME


@given(pathlib_path())
def test_Mod_build_mod_config_path(path: Path):
    """Ensure Mod builds the correct mod config path given a base directory."""

    built_path = Mod.build_mod_config_path(path)
    assert built_path.name == MOD_CONFIG_NAME
    assert built_path.parent.name == MOD_DIRECTORY_NAME
    assert built_path == path / MOD_DIRECTORY_NAME / MOD_CONFIG_NAME


@given(minimal_mod_config_payload())
def test_Mod_repr(payload: dict):
    """Ensure Mod string representation doesn't change without tests being aware."""

    with TemporaryDirectory() as temp_dirname:
        mod = Mod.create(dirpath=Path(temp_dirname), **payload)

        assert repr(mod) == (
            f"{mod.__class__.__qualname__!s}("
            f"name={mod.config.name!s}, version={mod.config.version!s})"
        )


@given(minimal_mod_config_payload())
def test_Mod_create(payload: dict):
    """Ensure Mod create classmethod works."""

    with TemporaryDirectory() as temp_dirname:
        temp_dirpath = Path(temp_dirname)
        mod = Mod.create(dirpath=temp_dirpath, **payload)

        assert isinstance(mod, Mod)

        assert mod.path == temp_dirpath
        assert mod.path.is_dir()
        assert mod.mod_dirpath == temp_dirpath / MOD_DIRECTORY_NAME
        assert mod.mod_dirpath.is_dir()
        assert mod.mod_config_path.is_file()

        assert isinstance(mod.config, ModConfig)


@given(pathlib_path(), minimal_mod_config_payload())
def test_Mod_create_raises_NotADirectoryError_with_invalid_directory(
    path: Path, payload: dict
):
    """Ensure Mod create classmethod raises NotADirectory with an invalid directory."""

    assume(not path.exists())
    with pytest.raises(NotADirectoryError):
        Mod.create(dirpath=path, **payload)


@given(minimal_mod_config_payload())
def test_Mod_create_raises_IsAMod_with_existing_mod(payload: dict):
    """Ensure Mod create classmethod raises IsAMod with a pre-existing mod."""

    with TemporaryDirectory() as temp_dirname:
        temp_dirpath = Path(temp_dirname)
        mod_dirpath = temp_dirpath / MOD_DIRECTORY_NAME
        mod_dirpath.mkdir()

        with pytest.raises(IsAMod):
            Mod.create(dirpath=temp_dirpath, **payload)


@patch("modist.core.mod.ModConfig")
@given(
    minimal_mod_config_payload(),
    builtin_exceptions(
        exclude=[UnicodeDecodeError, UnicodeEncodeError, UnicodeTranslateError]
    ),
)
def test_Mod_create_reraises_on_unexpected_exceptions(
    mocked_ModConfig, payload: dict, exc: Type[Exception]
):
    """Ensure Mod create classmethod reraises unexpected exceptions."""

    mocked_ModConfig.side_effect = exc
    with TemporaryDirectory() as temp_dirname:
        with pytest.raises(exc):
            Mod.create(dirpath=Path(temp_dirname), **payload)


@patch("modist.core.mod.ModConfig")
@given(
    minimal_mod_config_payload(),
    builtin_exceptions(
        exclude=[UnicodeDecodeError, UnicodeEncodeError, UnicodeTranslateError]
    ),
)
def test_Mod_create_cleans_up_mod_directory_on_unexpected_exceptions(
    mocked_ModConfig, payload: dict, exc: Type[Exception]
):
    """Ensure Mod create classmethod cleans up created mod directory on exceptions."""

    mocked_ModConfig.side_effect = exc
    with TemporaryDirectory() as temp_dirname:
        temp_dirpath = Path(temp_dirname)
        mod_dirpath = temp_dirpath / MOD_DIRECTORY_NAME

        with pytest.raises(exc):
            Mod.create(dirpath=temp_dirpath, **payload)
            assert not mod_dirpath.exists()


@given(minimal_mod_config_payload())
def test_Mod_from_dir(payload: dict):
    """Ensure Mod from_dir classmethod works."""

    with TemporaryDirectory() as temp_dirname:
        mod = Mod.create(dirpath=Path(temp_dirname), **payload)
        assert mod == Mod.from_dir(dirpath=mod.path)


@given(pathlib_path())
def test_Mod_from_dir_raises_NotADirectoryError_with_invalid_directory(path: Path):
    """Ensure Mod from_dir classmethod raises NotADirectory with invalid directory."""

    assume(not path.exists())
    with pytest.raises(NotADirectoryError):
        Mod.from_dir(dirpath=path)


@given(minimal_mod_config_payload())
def test_Mod_from_dir_raises_NotAMod_with_missing_mod_directory(payload: dict):
    """Ensure Mod from_dir classmethod raises NotAMod with missing mod directory."""

    with TemporaryDirectory() as temp_dirname:
        mod = Mod.create(dirpath=Path(temp_dirname), **payload)
        shutil.rmtree(mod.mod_dirpath)

        with pytest.raises(NotAMod):
            Mod.from_dir(dirpath=mod.path)


@given(minimal_mod_config_payload())
def test_Mod_from_dir_raises_NotAMod_with_missing_mod_config(payload: dict):
    """Ensure Mod from_dir classmethod raises NotAMod with missing mod config."""

    with TemporaryDirectory() as temp_dirname:
        mod = Mod.create(dirpath=Path(temp_dirname), **payload)
        os.remove(mod.mod_config_path)

        with pytest.raises(NotAMod):
            Mod.from_dir(dirpath=mod.path)


@pytest.mark.skipif(
    ctx.system.is_windows,
    reason="os specific test only works on Posix compatable systems",
)
@given(minimal_mod_config_payload())
def test_Mod_from_dir_fixes_invalid_mod_directory_mode(payload: dict):
    """Ensure Mod from_dir classmethod fixes mod directory with invalid stat mode."""

    # TODO: Need to find the appropriate method for testing this directory mod in
    # NT-based systems as their st_mode mask is confusing to me

    with TemporaryDirectory() as temp_dirname:
        mod = Mod.create(dirpath=Path(temp_dirname), **payload)
        mod.mod_dirpath.chmod(0o555)

        Mod.from_dir(dirpath=mod.path)
        assert mod.mod_dirpath.stat().st_mode & ((1 << 12) - 1) == MOD_DIRECTORY_MODE
