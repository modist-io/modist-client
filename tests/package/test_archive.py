# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""Contains unit-tests for package archive functions."""

import tarfile
from io import BytesIO, StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from hypothesis import given, settings
from hypothesis.strategies import DataObject, data, just, sampled_from
from wcmatch.pathlib import BRACE, GLOBSTAR, NEGATE

from modist import exceptions
from modist.config.manifest import ManifestConfig
from modist.context import instance as ctx
from modist.core.mod import MOD_DIRECTORY_NAME, Mod
from modist.package import archive, hasher

from ..config.strategies import manifest_config
from ..conftest import temporary_directory, temporary_filepath
from ..core.strategies import fake_mod, real_mod
from ..strategies import pathlib_path
from .conftest import temporary_mod_archive
from .strategies import hash_hexdigest, hash_type

TEST_DIRECTORY_PATH = Path(__file__).parent.parent
WCMATCH_GLOB_FLAGS = BRACE | GLOBSTAR | NEGATE


def test_walk_directory_artifacts():
    """Ensure walk_directory_artifacts works as expected."""

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
    """Ensure walk_directory_artifacts uses default arguments for glob."""

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
    """Ensure walk_directory_artifacts uses appropriate patterns in glob."""

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
    """Ensure walk_directory_artifacts only yields files."""

    for filepath in archive.walk_directory_artifacts(TEST_DIRECTORY_PATH):
        assert filepath.is_file()


@pytest.mark.fs
@pytest.mark.expensive
@settings(max_examples=10)
@given(data())
def test_build_manifest(data: DataObject):
    """Ensure build_manifest work as expected."""

    with temporary_directory("build_manifest") as temp_dirpath:
        mod: Mod = data.draw(real_mod(temp_dirpath))

        manifest = archive.build_manifest(mod)
        assert isinstance(manifest, ManifestConfig)
        assert len(manifest.artifacts) == len(list(mod.path.iterdir()))


@given(fake_mod(), sampled_from(archive.ArchiveType))
def test_build_archive_name(mod: Mod, archive_type: archive.ArchiveType):
    """Ensure build_archive_name works as expected."""

    # NOTE: this test is super explicit and doesn't really define any failing conditions
    # this test is only used for testing consistency, just in case build_archive_name
    # gets updated
    archive.build_archive_name(
        mod
    ) == f"{mod.config.name!s}-{mod.config.version!s}.tar.{archive_type.value!s}"


def test_build_manifest_name():
    """Ensure build_manifest_name works as expected."""

    # NOTE: this test is super explicit and doesn't really define any failing conditions
    # this test is only used for testing consistency, just in case build_manifest_name
    # gets updated
    assert (
        archive.build_manifest_name()
        == f"{MOD_DIRECTORY_NAME!s}/{archive.MANIFEST_NAME!s}"
    )


@given(manifest_config())
def test_build_manifest_info(manifest_config: ManifestConfig):
    """Ensure build_manifest_info works as expected."""

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


@pytest.mark.fs
@pytest.mark.expensive
@settings(max_examples=10)
@given(data(), sampled_from(archive.ArchiveType), hash_type())
def test_create_archive(
    data: DataObject, archive_type: archive.ArchiveType, hash_type: hasher.HashType
):
    """Ensure create_archive work as expected."""

    with temporary_mod_archive(
        data, archive_type=archive_type, hash_type=hash_type
    ) as (_, archive_path):
        assert archive_path.is_file()
        assert tarfile.is_tarfile(archive_path.as_posix())


@pytest.mark.fs
@given(fake_mod(), pathlib_path())
def test_create_archive_raises_FileExistsError_with_existing_output_filepath(
    mod: Mod, to_path: Path
):
    """Ensure create_archive raise FileExistsError with existing output path."""

    with temporary_directory(
        "create_archive_raises_FileExistsError_with_existing_output_filepath"
    ) as temp_dirpath:
        to_path = temp_dirpath / to_path

        if not to_path.parent.is_dir():
            to_path.parent.mkdir(parents=True)

        to_path.touch()

        with pytest.raises(FileExistsError):
            archive.create_archive(mod, to_path=to_path)


@given(fake_mod(), pathlib_path())
def test_create_archive_raises_NotADirectoryError_with_missing_output_directory(
    mod: Mod, to_path: Path
):
    """Ensure create_archive raise NotADirectoryError with missing output parent dir."""

    with pytest.raises(NotADirectoryError):
        archive.create_archive(mod, to_path=to_path)


@pytest.mark.fs
@given(fake_mod(), manifest_config())
def test_create_archive_reraises_FileNotFoundErrror_on_missing_artifact(
    mod: Mod, manifest: ManifestConfig
):
    """Ensure create_archive reraises FileNotFoundError from tarfile."""

    with temporary_directory(
        "create_archive_reraises_FileNotFoundError_on_missing_artifact"
    ) as temp_dirpath:
        to_path = temp_dirpath / "test-archive"

        with patch.object(archive, "build_manifest") as mocked_build_manifest:
            mocked_build_manifest.return_value = manifest

            with pytest.raises(FileNotFoundError):
                archive.create_archive(mod, to_path=to_path)

            # make sure unlink removes created archive on failure
            assert not to_path.exists()


@pytest.mark.fs
@pytest.mark.expensive
@settings(max_examples=10)
@given(data())
def test_verify_is_archive(data: DataObject):
    """Ensure verify_is_archive works as expected."""

    with temporary_mod_archive(data) as (_, archive_path):
        assert archive.verify_is_archive(archive_path=archive_path) is None


@given(pathlib_path())
def test_verify_is_archive_raises_FileNotFoundError_with_invalid_archive_path(
    archive_path: Path,
):
    """Ensure verify_is_archive raises FileNotFoundError with invalid path."""

    with pytest.raises(FileNotFoundError):
        archive.verify_is_archive(archive_path)


@pytest.mark.fs
def test_verify_is_archive_raises_NotAnArchive_with_invalid_archive():
    """Ensure verify_is_archive raises NotAnArchive with invalid archive."""

    with temporary_filepath(
        "verify_is_archive_raises_NotAnArchive_with_invalid_archive"
    ) as temp_filepath:
        with pytest.raises(exceptions.NotAnArchive):
            archive.verify_is_archive(temp_filepath)


@pytest.mark.fs
def test_verify_is_archive_raises_BadArchive_with_non_mod_archive():
    """Ensure verify_is_archive raises BadArchive with non-mod archive."""

    with temporary_filepath(
        "verify_is_archive_raises_BadArchive_with_non_mo_archive"
    ) as temp_filepath:
        tar = tarfile.open(temp_filepath.as_posix(), "w")
        tar.close()

        with pytest.raises(exceptions.BadArchive):
            archive.verify_is_archive(temp_filepath)


@pytest.mark.fs
@pytest.mark.expensive
@settings(max_examples=10)
@given(data(), sampled_from(archive.ArchiveType), hash_type())
def test_read_manifest(
    data: DataObject, archive_type: archive.ArchiveType, hash_type: hasher.HashType
):
    """Ensure read_manifest works as expected."""

    with temporary_mod_archive(
        data, archive_type=archive_type, hash_type=hash_type
    ) as (_, archive_path):
        manifest_info, manifest = archive.read_manifest(archive_path=archive_path)
        assert isinstance(manifest_info, tarfile.TarInfo)
        assert manifest_info.name == archive.build_manifest_name()
        assert isinstance(manifest, ManifestConfig)


@pytest.mark.fs
def test_read_manifest_raises_BadArchive_on_failure_to_find_manifest():
    """Ensure read_manifest raises BadArchive on missing manifest."""

    with temporary_filepath(
        "read_manifest_raises_BadArchive_on_failure_to_find_manifest"
    ) as temp_filepath:
        tar = tarfile.open(temp_filepath.as_posix(), "w")
        tar.close()

        with patch.object(archive, "verify_is_archive") as mocked_verify_is_archive:
            mocked_verify_is_archive.return_value = None

            with pytest.raises(exceptions.BadArchive):
                archive.read_manifest(archive_path=temp_filepath)


@pytest.mark.fs
@pytest.mark.expensive
@settings(max_examples=10)
@given(data())
def test_read_manifest_raises_BadArchive_on_failure_to_extract_manifest(
    data: DataObject,
):
    """Ensure read_manifest raises BadArchive on failed extract of manifest."""

    with temporary_mod_archive(data) as (_, archive_path):
        with patch.object(archive.tarfile.TarFile, "extractfile") as mocked_extractfile:
            mocked_extractfile.return_value = None

            with pytest.raises(exceptions.BadArchive):
                archive.read_manifest(archive_path=archive_path)


@pytest.mark.fs
@pytest.mark.expensive
@settings(max_examples=10)
@given(data())
def test_read_manifest_raises_BadArchive_on_failure_to_parse_manifest(data: DataObject):
    """Ensure read_manifest raises BadArchive on failed parse of manifest."""

    with temporary_mod_archive(data) as (_, archive_path):
        with patch.object(archive.tarfile.TarFile, "extractfile") as mocked_extractfile:
            mocked_extractfile.return_value = StringIO("")

            with pytest.raises(exceptions.BadArchive):
                archive.read_manifest(archive_path=archive_path)


@pytest.mark.fs
@pytest.mark.expensive
@settings(max_examples=10)
@given(data(), sampled_from(archive.ArchiveType), hash_type())
def test_verify_archive_artifact(
    data: DataObject, archive_type: archive.ArchiveType, hash_type: hasher.HashType
):
    """Ensure verify_archive_artifact works as expected.

    This test is very derivative and not required if ``test_verify_archive`` works.
    However, since this method is a public method, I feel that it's better to have a
    test case explicitly for it.
    """

    with temporary_mod_archive(
        data, archive_type=archive_type, hash_type=hash_type
    ) as (_, archive_path):
        _, manifest = archive.read_manifest(archive_path)
        with tarfile.open(archive_path.as_posix(), "r:*") as tar:
            for artifact_name, artifact_checksum in manifest.artifacts.items():
                artifact_info = tar.getmember(artifact_name)

                assert (
                    archive.verify_archive_artifact(
                        archive_io=tar,
                        artifact_info=artifact_info,
                        checksum=artifact_checksum,
                        hash_type=hash_type,
                    )
                    is None
                )


def test_verify_archive_artifact_raises_BadArchive_on_failure_to_extract_artifact():
    """Ensure verify_archive_artifact raises BadArchive with failed extraction."""

    tar_io = MagicMock()
    tar_io.extractfile.return_value = None

    with pytest.raises(exceptions.BadArchive):
        with patch.object(archive, "hash_io") as mocked_hash_io:
            mocked_hash_io.return_value = {}
        archive.verify_archive_artifact(tar_io, None, None)


@given(data(), hash_type())
def test_verify_archive_artifact_raises_BadArchive_on_mismatched_checksum(
    data: DataObject, hash_type: hasher.HashType,
):
    """Ensure verify_archive_artifact raises BadArchive on mismatched checksums."""

    tar_io = MagicMock()
    tar_io.extractfile.return_value = BytesIO(b"test")

    with patch.object(archive, "hash_io") as mocked_hash_io:
        mocked_hash_io.return_value = {hash_type: None}

        with pytest.raises(exceptions.BadArchive):
            archive.verify_archive_artifact(
                tar_io,
                tarfile.TarInfo("test"),
                checksum=data.draw(hash_hexdigest(hash_type_strategy=just(hash_type))),
                hash_type=hash_type,
            )


@pytest.mark.fs
@pytest.mark.expensive
@settings(max_examples=10)
@given(data(), sampled_from(archive.ArchiveType), hash_type())
def test_verify_archive(
    data: DataObject, archive_type: archive.ArchiveType, hash_type: hasher.HashType
):
    """Ensure verify_archive works as expected."""

    with temporary_mod_archive(
        data, archive_type=archive_type, hash_type=hash_type
    ) as (_, archive_path):
        assert archive.verify_archive(archive_path) is None


@pytest.mark.fs
@pytest.mark.expensive
@settings(max_examples=10)
@given(data())
def test_verify_archive_raises_BadArchive_on_unexpected_artifact(data: DataObject):
    """Ensure verify_archive raises BadArchive on unexpected artifacts."""

    with temporary_mod_archive(data) as (_, archive_path):
        manifest_info, manifest = archive.read_manifest(archive_path)
        # drop first entry from manifest so we can trigger the unexpected state
        manifest.artifacts.pop(list(manifest.artifacts.keys())[0])
        with patch.object(archive, "read_manifest") as mocked_read_manifest:
            mocked_read_manifest.return_value = (manifest_info, manifest)

            with pytest.raises(exceptions.BadArchive):
                archive.verify_archive(archive_path)


@pytest.mark.fs
@pytest.mark.expensive
@settings(max_examples=10)
@given(data())
def test_verify_archive_raises_BadArchive_on_unsafe_artifact(data: DataObject):
    """Ensure verify_archive raises BadArchive on unsafe archived names."""

    with temporary_mod_archive(data) as (_, archive_path):
        for bad_prefix in ("/", "..", "../"):
            manifest_info, manifest = archive.read_manifest(archive_path)
            with patch.object(archive, "read_manifest") as mocked_read_manifest:
                # overwrite artifacts to use invalid / unsafe prefixes for archive names
                mocked_read_manifest.return_value = (
                    manifest_info,
                    ManifestConfig(
                        artifacts={f"{bad_prefix!s}test": "test"},
                        hash_type=manifest.hash_type,
                    ),
                )
                with patch.object(
                    archive.tarfile.TarFile, "getmembers"
                ) as mocked_getmembers:
                    # overwrite also needs to occur in iteration of archive members
                    mocked_getmembers.return_value = [
                        tarfile.TarInfo(name=f"{bad_prefix!s}test")
                    ]

                    with pytest.raises(exceptions.BadArchive):
                        archive.verify_archive(archive_path)


@pytest.mark.fs
@pytest.mark.expensive
@settings(max_examples=10)
@given(data())
def test_extract_archive(data: DataObject):
    """Ensure extract_archive works as expected."""

    with temporary_mod_archive(data) as (mod, archive_path):
        with patch.object(
            archive, "verify_archive", wraps=archive.verify_archive
        ) as mocked_verify_archive:
            with temporary_directory("extract_archive") as output_dirpath:
                assert (
                    archive.extract_archive(archive_path, output_dirpath)
                    == output_dirpath
                )
                mocked_verify_archive.assert_called_once()

                # verify matching directory structures
                assert [
                    filepath.relative_to(mod.path).as_posix()
                    for filepath in mod.path.iterdir()
                ] == [
                    filepath.relative_to(output_dirpath).as_posix()
                    for filepath in output_dirpath.iterdir()
                ]


@pytest.mark.fs
@pytest.mark.expensive
@settings(max_examples=10)
@given(data())
def test_extract_archive_without_verification(data: DataObject):
    """Ensure extract_archive works as expected without pre-verification."""

    with temporary_mod_archive(data) as (mod, archive_path):
        with patch.object(
            archive, "verify_is_archive", wraps=archive.verify_is_archive
        ) as mocked_verify_is_archive:
            with temporary_directory(
                "extract_archive_without_verification"
            ) as output_dirpath:
                assert (
                    archive.extract_archive(archive_path, output_dirpath, verify=False)
                    == output_dirpath
                )
                mocked_verify_is_archive.assert_called_once()

                # verify matching directory structures
                assert [
                    filepath.relative_to(mod.path).as_posix()
                    for filepath in mod.path.iterdir()
                ] == [
                    filepath.relative_to(output_dirpath).as_posix()
                    for filepath in output_dirpath.iterdir()
                ]


@given(pathlib_path(), pathlib_path())
def test_extract_archive_raises_NotADirectoryError_with_invalid_output_directory(
    archive_path: Path, output_dir: Path
):
    """Ensure extract_archive raises NotADirectoryError with missing output dir."""

    with pytest.raises(NotADirectoryError):
        archive.extract_archive(archive_path, output_dir)
