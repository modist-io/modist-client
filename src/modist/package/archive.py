# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""This module provides functions to handle archiving a Mod for distribution.

We support all of the currently available tar compression algorithms from :mod:`tarfile`
and deal with manifest and checksum generation by default.

.. caution:: Although it is very easy to override the default archive type and the
    default archive checksum (hash) type, it is **highly discouraged** that you do so.
    Since many remote APIs will be expecting the default archive format, overriding
    these may cause the upload / publish of the mod archive to fail.

The available archive and checksum hash type options here are purely for 1-off use cases
where the remote API is either using a newer distribution format (or a deprecated one).

Otherwise, almost all usage of this module should look like the following:

>>> from pathlib import Path
>>> from modist.core import Mod
>>> mod = Mod.from_dir(Path("/A/PATH/TO/A/MOD/"))
>>> from modist.package.archive import create_archive, verify_archive
>>> archive_path = create_archive(mod)
>>> archive_path
Path("/CURRENT/WORKING/DIRECTORY/my-mod-x.x.x.tar.xz")
>>> verify_archive(archive_path)  # will raise BadArchive on tampered / invalid archives
None
"""

import concurrent.futures
import functools
import re
import tarfile
import time
from enum import Enum
from io import BytesIO
from pathlib import Path
from typing import Dict, Generator, Optional, Set, Tuple

from wcmatch import pathlib as wcmatch_pathlib

from ..config.manifest import ManifestConfig
from ..context import instance as ctx
from ..core.mod import MOD_DIRECTORY_NAME, Mod
from ..exceptions import BadArchive, NotAnArchive
from ..log import instance as log
from .hasher import HashType, hash_file, hash_io


class ArchiveType(Enum):
    """Enumeration of supported archive types."""

    GZIP = "gz"
    BZIP2 = "bz2"
    LZMA = "xz"


MANIFEST_NAME = "manifest.json"
MANIFEST_MODE = 0o655
DEFAULT_MANIFEST_INCLUDE = {"*"}
DEFAULT_ARCHIVE_TYPE = ArchiveType.LZMA
DEFAULT_ARCHIVE_HASH_TYPE = HashType.XXHASH

UNSAFE_ARTIFACT_NAME_PATTERN = re.compile(r"^/|\.{2,}")


def walk_directory_artifacts(
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

    >>> from modist.package.archive import walk_directory_artifacts
    >>> for filepath in walk_directory_artifacts(
    ...     Path("/some/directory"),
    ...     include={"*.{t,j}s"}
    ... ):
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
        include = DEFAULT_MANIFEST_INCLUDE
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
) -> ManifestConfig:
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
    :rtype: ~modist.config.manifest.ManifestConfig
    """

    log.info(f"building archive manifest for {mod!r}")
    artifacts: Dict[str, str] = {}

    # we always include all details in the mod metadata directory in the manifest
    for filepath in walk_directory_artifacts(
        mod.mod_dirpath, include=DEFAULT_MANIFEST_INCLUDE
    ):
        artifacts[filepath.relative_to(mod.path).as_posix()] = hash_file(
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
        for filepath in walk_directory_artifacts(
            mod.path, include=set(mod.config.include), exclude=set(mod.config.exclude)
        ):
            submitted_future = executor.submit(hash_file, filepath, {hash_type})
            future_map[submitted_future] = filepath

        for future in concurrent.futures.as_completed(future_map):
            relative_pathname = future_map[future].relative_to(mod.path).as_posix()
            artifacts[relative_pathname] = future.result()[hash_type]

    return ManifestConfig(artifacts=artifacts, hash_type=hash_type)


def build_archive_name(
    mod: Mod, archive_type: ArchiveType = DEFAULT_ARCHIVE_TYPE
) -> str:
    """Build the appropriate archive filename for the given mod.

    :param ~modist.core.Mod mod: The mod to build the archive filename for
    :param ArchiveType archive_type: The type of archive being built
        (this is used to generate an appropriate subextension),
        optional, defaults to ``DEFAULT_ARCHIVE_TYPE``
    :return: A filename string for the given mod's archive
    :rtype: str
    """

    return f"{mod.config.name!s}-{mod.config.version!s}.tar.{archive_type.value!s}"


def build_manifest_name() -> str:
    """Build the appropriate archive manifest's archive name.

    :return: A archive filename for the mod's manifest
    :rtype: str
    """

    return f"{MOD_DIRECTORY_NAME!s}/{MANIFEST_NAME!s}"


def build_manifest_info(manifest: ManifestConfig) -> Tuple[tarfile.TarInfo, BytesIO]:
    """Build the appropriate archive manifest's tar info record.

    The output of this function results in both the appropriate
    :class:`~tarfile.TarInfo` record and the :class:`~io.BytesIO` buffer that should be
    used to add the manifest into the archive. Usage should almost always look like the
    following:

    >>> import tarfile
    >>> from modist.package.archive import build_manifest_info, build_manifest
    >>> with tarfile.open("/SOME/MOD/DIRECTORY/archive.tar.gz", "w:gz") as tar:
    ...     tar.addfile(*build_manifest_info(build_manifest(mod)))


    :param ~modist.config.manifest.ManifestConfig manifest: The manifest instance
    :return: A tuple of the manifest's tar record and the io buffer that should be used
        to write the manifest into the archive
    :rtype: Tuple[~tarfile.TarInfo, ~io.BytesIO]
    """

    manifest_content = bytes(manifest.to_json(), "utf-8")
    manifest_tarinfo = tarfile.TarInfo(name=build_manifest_name())

    manifest_tarinfo.size = len(manifest_content)
    manifest_tarinfo.type = tarfile.REGTYPE
    manifest_tarinfo.mtime = int(time.time())
    manifest_tarinfo.mode = MANIFEST_MODE
    manifest_tarinfo.uname = ctx.system.user.username

    return manifest_tarinfo, BytesIO(manifest_content)


def create_archive(
    mod: Mod,
    to_path: Optional[Path] = None,
    archive_type: ArchiveType = DEFAULT_ARCHIVE_TYPE,
    hash_type: HashType = DEFAULT_ARCHIVE_HASH_TYPE,
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
    :param ArchiveType archive_type: The type of compression algorithm to use for
        building the archive, optional, defaults to ``DEFAULT_ARCHIVE_TYPE``
    :param ~modist.package.hasher.HashType hash_type: The type of hashing algorithm to
        use for producing checksums for mod artifacts in the manifest, optional,
        defaults to ``DEFAULT_ARCHIVE_HASH_TYPE``
    :raises FileExistsError: If the given ``to_path`` already exists
    :raises NotADirectoryError: The given parent of the given ``to_path`` does not exist
    :return: The path to where the archive was written
    :rtype: ~pathlib.Path
    """

    output_path: Path = (
        ctx.system.cwd / build_archive_name(mod=mod, archive_type=archive_type)
    ) if not to_path else to_path
    log.info(
        f"creating {archive_type!r} archive for {mod!r} at {output_path!r} using "
        f"{hash_type!r} checksums"
    )

    if output_path.is_file():
        raise FileExistsError(f"file {output_path!r} already exists")

    if not output_path.parent.is_dir():
        raise NotADirectoryError(f"no such directory {output_path.parent!r} exists")

    manifest = build_manifest(mod, hash_type=hash_type)
    try:
        with tarfile.open(output_path, f"w:{archive_type.value!s}") as tar:
            for artifact_name in manifest.artifacts.keys():
                fullpath = mod.path / artifact_name
                log.debug(
                    f"adding {fullpath!r} to the archive at {output_path!r} using "
                    f"archived name {artifact_name!r}"
                )
                tar.add(name=fullpath.as_posix(), arcname=artifact_name)

            # NOTE: we should always be writing manifest details into the archive last
            manifest_info, manifest_io = build_manifest_info(manifest=manifest)
            log.debug(
                f"adding manifest to the archive at {output_path!r} using "
                f"archived name {manifest_info.name!r}"
            )
            tar.addfile(tarinfo=manifest_info, fileobj=manifest_io)

        log.success(f"created archive for {mod!r} at {output_path!r}")
        return output_path
    except FileNotFoundError:
        log.info(f"removing created archive at {output_path!r} due to raised exception")
        # FIXME: potential for PermissionsError on Windows
        output_path.unlink()
        raise


@functools.lru_cache()
def verify_is_archive(archive_path: Path):
    """Verify a given path to an archive is actually an existing archive.

    :param ~pathlib.Path archive_path: The path to the archive
    :raises FileNotFoundError: If the given ``archive_path`` is not an existing file
    :raises NotAnArchive: If the given ``archive_path`` is not determined as parseable
        by :mod:`tarfile` via :func:`tarfile.is_tarfile`
    """

    log.info(f"verifying archive at {archive_path!r} is an archive")
    if not archive_path.is_file():
        raise FileNotFoundError(f"no such file {archive_path!r} exists")

    if not tarfile.is_tarfile(archive_path.as_posix()):
        raise NotAnArchive(f"file {archive_path!r} is not an archive")

    # TODO: this is a little too expensive for building a set, and I don't necessarily
    # like the logic being used to build the mod config path here...
    required_archive_names: Set[str] = {
        build_manifest_name(),
        Mod.build_mod_config_path(Path()).as_posix(),
    }

    with tarfile.open(archive_path.as_posix(), "r:*") as tar:
        if len(required_archive_names & set(tar.getnames())) != len(
            required_archive_names
        ):
            raise BadArchive(
                f"archive at {archive_path!r} does not appear to be a mod archive"
            )


def read_manifest(archive_path: Path) -> Tuple[tarfile.TarInfo, ManifestConfig]:
    """Read the manifest content's from a given archive.

    :param ~pathlib.Path archive_path: The path of the archive to read the manifest from
    :raises NotAnArchive: If the given archive doesn't appear to be a mod archive
    :raises BadArchive: If the extraction of the manifest from the archive fails
    :return: A tuple of the manifest's tar info and the manifest dictionary
    :rtype: Tuple[~tarfile.TarInfo, ~modist.config.manifest.ManifestConfig]
    """

    verify_is_archive(archive_path)

    # transparent compression is determined by `r:*`, don't switch this out for `r|*` as
    # we need to be able to do backwards seeks in the tarfile io buffer
    with tarfile.open(archive_path.as_posix(), "r:*") as tar:
        try:
            manifest_info = tar.getmember(name=build_manifest_name())
        except KeyError:
            # NOTE: this shouldn't ever happen if we sucessfully get past
            # `verify_is_archive`. however, it is still an edge case if the buffer is
            # cut short in memory for some reason
            raise BadArchive(
                f"failed to extract manifest info from archive at {archive_path!r}"
            )

        log.debug(
            f"reading manifest from {manifest_info!r} from archive at {archive_path!r}"
        )
        manifest_io = tar.extractfile(member=manifest_info)
        if not manifest_io:
            raise BadArchive(
                f"failed to extract manifest from archive at {archive_path!r}"
            )

        try:
            return (
                manifest_info,
                ManifestConfig.from_json(manifest_io.read().decode("utf-8")),
            )
        except Exception as exc:
            raise BadArchive(
                f"failed to parse manifest from archive at {archive_path!r}"
            ) from exc


def verify_archive_artifact(
    archive_io: tarfile.TarFile,
    artifact_info: tarfile.TarInfo,
    checksum: str,
    hash_type: HashType = DEFAULT_ARCHIVE_HASH_TYPE,
):
    """Verify a given artifact buffer is valid against the manifest.

    :param ~tarfile.TarFile archive_io: The tarfile IO containing the artifact
    :param ~tarfile.TarInfo artifact_info: The tar info for this artifact
    :param str checksum: The manifest checksum of this artifact
    :param HashType hash_type: The type of hashing algorithm the archive's manifest is
        using, optional, defaults to ``DEFAULT_ARCHIVE_HASH_TYPE``
    :raises BadArchive: When we fail to extract the requested ``artifact_info`` from
        the given ``archive_io``
    :raises BadArchive: When the manifest checksum of an artifact doesn't match
        the extracted artifact's checksum
    """

    artifact_io = archive_io.extractfile(artifact_info)
    if not artifact_io:
        raise BadArchive(f"failed to extract artifact {artifact_info!r}")

    artifact_checksum = hash_io(artifact_io, {hash_type})[hash_type]
    log.info(
        f"checking artifact {artifact_info!r} checksum {artifact_checksum!r} matches "
        f"manifest checksum {checksum!r}"
    )
    if checksum != artifact_checksum:
        raise BadArchive(
            f"checksum {artifact_checksum!r} is invalid for artifact "
            f"{artifact_info!r}, expected {checksum!r}"
        )


def verify_archive(archive_path: Path, max_workers: Optional[int] = None):
    """Verify a given archive is a valid mod's archive.

    :param ~pathlib.Path archive_path: The path to the archive to validate
    :param Optional[int] max_workers: The maximum number of thread workers to process
        artifact checksums with
    :raises FileNotFoundError: If the given ``archive_path`` doesn't exist
    :raises NotAnArchive: If the given ``archive_path`` is not determined as parseable
        by :mod:`tarfile` via :func:`tarfile.is_tarfile`
    :raises BadArchive: When the extraction of the mod manifest fails
    :raises BadArchive: When an unexpected artifact (not in the manifest) is encountered
    :raises BadArchive: When the extraction of an artifact fails
    :raises BadArchive: When the manifest checksum of an artifact doesn't match the
        extracted artifact's checksum
    """

    log.info(f"verifying archive at {archive_path!r}")
    manifest_info, manifest = read_manifest(archive_path)

    # transparent compression is determined by `r:*`, DON't SWITCH THIS OUT for `r|*` as
    # we need to be able to do backwards seeks in the tarfile buffer
    with tarfile.open(archive_path.as_posix(), "r:*") as tar:

        # filtering out the manifest from the fetched archive members as it is
        # impossible to add the manifest's checksum to the manifest
        for artifact_info in filter(
            lambda member: member.name != manifest_info.name, tar.getmembers()
        ):
            log.debug(
                f"verifying artifact {artifact_info!r} from archive at {archive_path!r}"
            )
            if artifact_info.name not in manifest.artifacts:
                raise BadArchive(f"unexpected artifact {artifact_info!r} in archive")

            # XXX: archives can potentially contain unsafe extraction names that extract
            # themselves to the local machine's root directory or outside of the target
            # directory when written with a name using either of the following prefixes:
            #   - "/"
            #   - ".."
            # We do a quick regex match here to ensure that the archived name doesn't
            # contain a name using one of these unsafe patterns
            if UNSAFE_ARTIFACT_NAME_PATTERN.match(artifact_info.name):
                raise BadArchive(f"unsafe artifact name {artifact_info!r} in archive")

            # we are building a multi-threaded artifact verification since we must
            # recalculate checksums which can be greatly benefited if split up when
            # dealing with archives containing large files
            future_map: Dict[concurrent.futures.Future, tarfile.TarInfo] = {}
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=(
                    max_workers if max_workers else (ctx.system.available_cpu_count - 1)
                )
            ) as executor:
                verify_future: concurrent.futures.Future = executor.submit(
                    verify_archive_artifact,
                    archive_io=tar,
                    artifact_info=artifact_info,
                    checksum=manifest.artifacts[artifact_info.name],
                    hash_type=manifest.hash_type,
                )
                future_map[verify_future] = artifact_info

            for future in concurrent.futures.as_completed(future_map):
                # all values returned from _verify_archive_artifact are None, we only
                # care if an exception is raised which we just need to re-raise
                future.result()

    log.success(f"archive at {archive_path!r} appears to be valid")


def extract_archive(archive_path: Path, output_dir: Path, verify: bool = True) -> Path:
    """Extract the contents of a given archive to an output directory.

    .. caution:: If you decide to disable archive pre-verification by toggling the
        ``verify`` flag to false, you may be in danger of the archive not only not being
        an tampered mod archive, but extracting the archive could potentially write
        files outside of the scope of the ``output_dir`` path.

        See the warning in :meth:`tarfile.TarFile.extractall`. Performing verification
        will take measures to prevent this before you attempt to extract all members
        from the archive to the provided output directory.


    :param ~pathlib.Path archive_path: The path to the archive to extract
    :param ~pathlib.Path output_dir: The path to the directory to write artifacts to
    :param bool verify: Flag that indicates if archive verification should occur before
        attempting to extract, optional, defaults to True
    :raises FileNotFoundError: If the given archive path does not exist
    :raises NotAnArchive: If the given archive path is not a path to an archive
    :raises BadArchive: If the given archive is determined to be invalid or unsafe
    :raises NotADirectoryError: If the given ``output_dir`` is not a valid directory
    :return: The directory the content of the archive was written to
    :rtype: ~pathlib.Path
    """

    log.info(f"extracting archive from {archive_path!r} to directory {output_dir!r}")
    if not output_dir.is_dir():
        raise NotADirectoryError(f"no such directory {output_dir!r} exists")

    if verify:
        verify_archive(archive_path)
    else:
        log.warning(
            f"skipping pre-verification of archive at {archive_path!r} before "
            "extracting artifacts, this is potentially very dangerous"
        )
        # at the very least we need to verify that we can process the given archive
        verify_is_archive(archive_path)

    with tarfile.open(archive_path, "r:*") as tar:
        log.debug(f"extracting all members from archive {tar!r} to {output_dir!r}")
        # NOTE: we are specifically not using tar.extract() per file due to several
        # extraction issues that have always existed in the tarfile builtin package.
        # See the tarfile tar.extract note on issues related to using extract()
        tar.extractall(path=output_dir)

    log.success(f"extracted archive from {archive_path!r} to directory {output_dir!r}")
    return output_dir
