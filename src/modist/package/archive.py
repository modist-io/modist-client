# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""This module provides functions to handle archiving a Mod for distribution.

We support all of the currently available tar compression algorithms from :mod:`tarfile`
and deal with manifest and checksum generation by default. Although it is very easy to
override the default archive type and the default archive checksum (hash) type, it is
**highly discouraged** that you do so. Since many remote APIs will be expecting the
default archive format, overriding these may cause the upload / publish of the mod
archive to fail.
The available archive and checksum hash type options here are purely for 1-off use cases
where the remote API is either using a newer distribution format (or a deprecated one).

Otherwise, almost all usage of this module should look like the following:

>>> from pathlib import Path
>>> from modist.core import Mod
>>> mod = Mod.from_dir(Path("/A/PATH/TO/A/MOD/"))
>>> from modist.package.archive import create_archive
>>> create_archive(mod)
Path("/CURRENT/WORKING/DIRECTORY/my-mod-x.x.x.tar.xz")
"""

import concurrent.futures
import os
import tarfile
import time
from enum import Enum
from io import BytesIO
from pathlib import Path
from typing import Dict, Generator, Optional, Set, Tuple

import rapidjson as json
from wcmatch import pathlib as wcmatch_pathlib

from ..context import instance as ctx
from ..core.mod import Mod
from ..log import instance as log
from .hasher import HashType, hash_file


class ArchiveType(Enum):
    """Enumeration of supported archive types."""

    GZIP = "gz"
    BZIP2 = "bzip"
    LZMA = "xz"


MANIFEST_NAME = "manifest.json"
DEFAULT_ARCHIVE_TYPE = ArchiveType.LZMA
DEFAULT_ARCHIVE_HASH_TYPE = HashType.XXHASH


def walk_directory(
    directory: Path,
    include: Optional[Set[str]] = None,
    exclude: Optional[Set[str]] = None,
) -> Generator[Path, None, None]:
    """Walk a directory recursively based on include and exclude globs.

    The provided glob patterns allow for `brace expansion <https://shorturl.at/efrJS>`_
    but are case-sensitive. This means that you can allow for multiple files within a
    single glob expression. This is powered through the use of
    `wcmatch <https://facelessuser.github.io/wcmatch/>`_.

    For example, if I wanted a single expression to include all ``.ts`` and ``.js``
    files, I could use the following expression:

    >>> from modist.package.archive import walk_directory
    >>> for filepath in walk_directory(Path("/some/directory"), include={"*.{t,j}s"}):
    >>>     print(filepath)


    .. caution:: It is always suggested that you supply at least one ``include`` glob
        pattern. If none are given, the ``include`` pattern will default to matching
        all potential files in the given ``directory``. This can pontentially be very
        expensive and take a while to walk depending on the size and depth of the
        provided ``directory``.

        If you do need to include all files in the directory but want to silence the
        logged warning, just supply ``{"*"}`` as the value for the ``include``
        keyword argument.

    :param ~pathlib.Path directory: The directory path to start the walk from
    :param Optional[Set[str]] include: A set of globs that indicate valid files,
        optional, defaults to None
    :param Optional[Set[str]] exclude: A set of globs that indicate invalid files,
        optional, defaults to None
    :raises NotADirectoryError: If the given ``directory`` does not exist
    :rtype: Generator[~pathlib.Path, None, None]
    """

    if not directory.is_dir():
        raise NotADirectoryError(f"no such directory {directory.as_posix()!r} exists")

    wc_path = wcmatch_pathlib.Path(directory).resolve()
    if not include:
        include = {"*"}
        log.warning(
            "no includes provided for directory walk, "
            f"defaulting to {include!r} which may be expensive"
        )
    if not exclude:
        exclude = set()

    patterns = include.union({f"!{exclude_glob!s}" for exclude_glob in exclude})
    for path in wc_path.rglob(
        patterns=patterns,
        flags=wcmatch_pathlib.GLOBSTAR | wcmatch_pathlib.NEGATE | wcmatch_pathlib.BRACE,
    ):
        if path.is_file():
            log.debug(f"yielding path {path!r}")
            yield path


def build_manifest(
    mod: Mod,
    max_workers: Optional[int] = None,
    hash_type: HashType = DEFAULT_ARCHIVE_HASH_TYPE,
) -> Dict[str, str]:
    """Build a manifest of artifacts from the given mod.

    .. tip:: If ``max_workers`` is not given, the executor will default to ``the number
        of available CPUs - 1``. The number of available CPUs is determined through the
        result of :func:`~modist.context.system.get_available_cpu_count` via the
        available context :data:`~modist.context.instance` variable.

    :param ~modist.core.Mod mod: The mod to build a manifest of artifacts for
    :param Optional[int] max_workers: The number of thread workers to allow for parallel
        hashing (useful for mods with large files), optional, defaults to None
    :param ~modist.package.hasher.HashType hash_type: The type of hashing algorithm to
        use for calculating artifact checksums, default to ``DEFAULT_ARCHIVE_HASH_TYPE``
    :return: A dictionary of artifact path to content hash
    :rtype: Dict[str, str]
    """

    log.info(f"building archive manifest for {mod!r}")
    manifest: Dict[str, str] = {}

    for filepath in walk_directory(mod.mod_dirpath, include={"*"}):
        manifest[filepath.relative_to(mod.path).as_posix()] = hash_file(
            filepath, {hash_type}
        )[hash_type]

    # we default to the count of available CPUs - 1 here in order to preserve a core to
    # continue handling the future building and scheduling
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=(
            max_workers if max_workers else (ctx.system.available_cpu_count - 1)
        )
    ) as executor:
        future_map: Dict[concurrent.futures.Future, Path] = {}
        for filepath in walk_directory(
            mod.path, include=set(mod.config.include), exclude=set(mod.config.exclude)
        ):
            submitted_future = executor.submit(hash_file, filepath, {hash_type})
            future_map[submitted_future] = filepath

        for future in concurrent.futures.as_completed(future_map):
            relative_pathname = future_map[future].relative_to(mod.path).as_posix()
            manifest[relative_pathname] = future.result()[hash_type]

    return manifest


def build_archive_name(
    mod: Mod, archive_type: ArchiveType = DEFAULT_ARCHIVE_TYPE
) -> str:
    """Build the appropriate archive filename for the given mod.

    :param ~modist.core.Mod mod: The mod to build the archive filename for
    :param ArchiveType archive_type: The type of archive being built
        (this is used to generate an appropriate subextension),
        optional, defaults to DEFAULT_ARCHIVE_TYPE
    :return: A filename string for the given mod's archive
    :rtype: str
    """

    return f"{mod.config.name!s}-{mod.config.version!s}.tar.{archive_type.value!s}"


def build_manifest_name(mod: Mod) -> str:
    """Build the appropriate archive manifest's archive name.

    :param ~modist.core.Mod mod: The mod the manifest refers to
    :return: A archive filename for the mod's manifest
    :rtype: str
    """

    return Path(*(mod.mod_dirpath / MANIFEST_NAME).parts[-2:]).as_posix()


def build_manifest_info(
    mod: Mod, manifest: Dict[str, str]
) -> Tuple[tarfile.TarInfo, BytesIO]:
    """Build the appropriate archive manifest's tar info record.

    The output of this function results in both the appropriate
    :class:`~tarfile.TarInfo` record and the :class:`~io.BytesIO` buffer that should be
    used to add the manifest into the archive. Usage should almost always look like the
    following:

    >>> import tarfile
    >>> from modist.package.archive import build_manifest_info, build_manifest
    >>> from modist.core import Mod
    >>> mod = Mod.from_dir("/SOME/MOD/DIRECTORY")
    >>> with tarfile.open("/SOME/MOD/DIRECTORY/archive.tar.gz", "w:gz") as tar:
    ...     tar.addfile(*build_manifest_info(build_manifest(mod)))


    :param ~modist.core.Mod mod: The mod the manifest refers to
    :param Dict[str, str] manifest: The manifest dictionary
    :return: A tuple of the manifest's tar record and the io buffer that should be used
        to write the manifest into the archive
    :rtype: Tuple[~tarfile.TarInfo, BytesIO]
    """

    log.debug(f"building custom tar info for manifest of {mod!r}")

    manifest_content = bytes(json.dumps(manifest), "utf-8")
    manifest_tarinfo = tarfile.TarInfo(name=build_manifest_name(mod))

    manifest_tarinfo.size = len(manifest_content)
    manifest_tarinfo.type = tarfile.REGTYPE
    manifest_tarinfo.mtime = int(time.time())
    manifest_tarinfo.mode = 0o655
    manifest_tarinfo.uname = ctx.system.user.username

    return manifest_tarinfo, BytesIO(manifest_content)


def create_archive(
    mod: Mod,
    to_path: Optional[Path] = None,
    archive_type: ArchiveType = DEFAULT_ARCHIVE_TYPE,
) -> Path:
    """Create an archive for the given mod.

    .. tip:: If no ``to_path`` is provided, this function will default the output path
        to a filename produced from :func:`~build_archive_name` in the current
        working directory. The value of the current working directory is pulled from
        the result of :func:`~modist.context.system.get_cwd` via the provided
        :data:`~modist.context.instance` variable.

    :param Mod mod: The mod to create an archive for
    :param Optional[~pathlib.Path] to_path: The path to write the archive to,
        optional, defaults to None
    :param ArchiveType archive_type: The type of hashing algorithm to use for producing
        checksums for mod artifacts in the manifest,
        optional, defaults to ``DEFAULT_ARCHIVE_TYPE``
    :raises FileExistsError: If the given ``to_path`` already exists
    :raises NotADirectoryError: The given parent of the given ``to_path`` does not exist
    :return: The path to where the archive was written
    :rtype: ~pathlib.Path
    """

    output_path: Path = (
        ctx.system.cwd / build_archive_name(mod=mod, archive_type=archive_type)
    ) if not to_path else to_path

    if output_path.is_file():
        raise FileExistsError(f"file {output_path!r} already exists")

    if not output_path.parent.is_dir():
        raise NotADirectoryError(f"no such directory {output_path.parent!r} exists")

    log.info(f"creating {archive_type!r} archive for {mod!r} at {output_path!r}")
    manifest = build_manifest(mod)
    try:
        with tarfile.open(output_path, f"w:{archive_type.value!s}") as tar:
            for path_name, checksum in manifest.items():
                fullpath = mod.path / path_name
                log.debug(
                    f"adding {fullpath!r} to the archive at {output_path!r} using "
                    f"archived name {path_name!r}"
                )
                tar.add(name=fullpath.as_posix(), arcname=path_name)

            # NOTE: we should always be writing manifest details into the archive last
            manifest_info, manifest_io = build_manifest_info(mod=mod, manifest=manifest)
            log.debug(
                f"adding manifest to the archive at {output_path!r} using "
                f"archived name {manifest_info.name!r}"
            )
            tar.addfile(tarinfo=manifest_info, fileobj=manifest_io)

        return output_path
    except FileNotFoundError:
        log.info(f"removing created archive at {output_path!r} due to raised exception")
        os.remove(output_path)
        raise
