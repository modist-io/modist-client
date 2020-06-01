# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""Contains pytest configuration and features for the package module tests."""

from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Tuple

from hypothesis.strategies import DataObject

from modist.core.mod import Mod
from modist.package.archive import (
    DEFAULT_ARCHIVE_HASH_TYPE,
    DEFAULT_ARCHIVE_TYPE,
    ArchiveType,
    create_archive,
)
from modist.package.hasher import HashType

from ..conftest import temporary_directory
from ..core.strategies import real_mod


@contextmanager
def temporary_mod(data: DataObject) -> Generator[Mod, None, None]:
    """Generate a temporary real mod in a temporary directory that dissapears.

    :param ~hypothesis.strategies.DataObject data: The base hypothesis data strategy
    """

    with temporary_directory("temporary_mod") as temp_dirpath:
        mod: Mod = data.draw(real_mod(parent_dir=temp_dirpath))
        yield mod


@contextmanager
def temporary_mod_archive(
    data: DataObject,
    archive_type: ArchiveType = DEFAULT_ARCHIVE_TYPE,
    hash_type: HashType = DEFAULT_ARCHIVE_HASH_TYPE,
) -> Generator[Tuple[Mod, Path], None, None]:
    """Generate a temporary mod and archive of the mod into temporary directories.

    :param ~hypothesis.strategies.DataObject data: The base hypothesis data strategy
    :param ~modist.package.archive.ArchiveType archive_type: The archive type to
        generate, optional, defaults to ``DEFAULT_ARCHIVE_TYPE``
    :param ~modist.package.hasher.HashType hash_type: The hash type to use for archive
        generation, optional, defaults to ``DEFAULT_ARCHIVE_HASH_TYPE``
    """

    with temporary_mod(data) as mod:
        with temporary_directory("temporary_mod_archive") as temp_dirpath:
            temp_filepath = temp_dirpath / "archive"

            archive_path = create_archive(
                mod,
                to_path=temp_filepath,
                archive_type=archive_type,
                hash_type=hash_type,
            )

            assert archive_path == temp_filepath
            yield mod, temp_filepath
