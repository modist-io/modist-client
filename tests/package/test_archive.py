# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""Contains unit-tests for package archive functions."""

import tarfile
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

import pytest
from hypothesis import given
from hypothesis.strategies import sampled_from
from wcmatch.pathlib import BRACE, GLOBSTAR, NEGATE

from modist.config.manifest import ManifestConfig
from modist.context import instance as ctx
from modist.core.mod import MOD_DIRECTORY_NAME, Mod
from modist.package import archive

from ..config.strategies import manifest_config
from ..core.strategies import mod
from ..strategies import pathlib_path

TEST_DIRECTORY_PATH = Path(__file__).parent.parent
WCMATCH_GLOB_FLAGS = BRACE | GLOBSTAR | NEGATE


def test_walk_directory_artifacts():
    """Ensure calls to walk_directory_artifacts works as expected."""

    for filepath in archive.walk_directory_artifacts(
        TEST_DIRECTORY_PATH, include={"test_*.py"}, exclude={"test_archive.py"}
    ):
        assert filepath.is_file()
        assert filepath.name.startswith("test_")
        assert filepath.name != "test_archive.py"


@given(pathlib_path())
def test_walk_directory_artifacts_raises_NotADirectoryError_with_invalid_path(
    directory: Path,
):
    """Ensure invalid calls to walk_directory_artifacts raises NotADirectorryError."""

    with pytest.raises(NotADirectoryError):
        next(archive.walk_directory_artifacts(directory))


def test_walk_directory_artifacts_defaults():
    """Ensure calls to walk_directory_artifacts uses default arguments for glob."""

    with patch.object(archive.wcmatch_pathlib.Path, "rglob") as mocked_rglob:
        # since we are mocking out rglob the generator will fail, but we really only
        # care about what the method is called with
        with pytest.raises(StopIteration):
            next(
                archive.walk_directory_artifacts(
                    TEST_DIRECTORY_PATH, include=None, exclude=None
                )
            )

        mocked_rglob.assert_called_once_with(flags=WCMATCH_GLOB_FLAGS, patterns={"*"})


def test_walk_directory_artifacts_builds_appropriate_include_exclude_patterns():
    """Ensure calls to walk_directory_artifacts uses appropriate patterns in glob."""

    with patch.object(archive.wcmatch_pathlib.Path, "rglob") as mocked_rglob:
        with pytest.raises(StopIteration):
            next(
                archive.walk_directory_artifacts(
                    TEST_DIRECTORY_PATH, include={"*.py"}, exclude={"*.pyc"}
                )
            )

        mocked_rglob.assert_called_once_with(
            flags=WCMATCH_GLOB_FLAGS, patterns={"*.py", "!*.pyc"}
        )


def test_walk_directory_artifacts_only_yields_files():
    """Ensure calls to walk_directory_artifacts only yields files."""

    for filepath in archive.walk_directory_artifacts(TEST_DIRECTORY_PATH):
        assert filepath.is_file()


@given(mod(), sampled_from(archive.ArchiveType))
def test_build_archive_name(mod: Mod, archive_type: archive.ArchiveType):
    """Ensure calls to build_archive_name works as expected."""

    # NOTE: this test is super explicit and doesn't really define any failing conditions
    # this test is only used for testing consistency, just in case build_archive_name
    # gets updated
    archive.build_archive_name(
        mod
    ) == f"{mod.config.name!s}-{mod.config.version!s}.tar.{archive_type.value!s}"


def test_build_manifest_name():
    """Ensure calls to build_manifest_name works as expected."""

    # NOTE: this test is super explicit and doesn't really define any failing conditions
    # this test is only used for testing consistency, just in case build_manifest_name
    # gets updated
    assert (
        archive.build_manifest_name()
        == f"{MOD_DIRECTORY_NAME!s}/{archive.MANIFEST_NAME!s}"
    )


@given(manifest_config())
def test_build_manifest_info(manifest_config: ManifestConfig):
    """Ensure calls to build_manifest_info works as expected."""

    manifest_info = archive.build_manifest_info(manifest_config)
    assert isinstance(manifest_info, tuple)
    assert len(manifest_info) == 2

    tar_info, content = manifest_info
    assert isinstance(tar_info, tarfile.TarInfo)
    assert isinstance(content, BytesIO)

    assert tar_info.size == len(bytes(manifest_config.to_json(), "utf-8"))
    assert tar_info.mode == archive.MANIFEST_MODE
    assert tar_info.type == tarfile.REGTYPE
    assert isinstance(tar_info.mtime, int)
    assert tar_info.uname == ctx.system.user.username
