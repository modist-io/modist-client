# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""Contains unit-tests for package hasher functions."""

import os
from io import BytesIO
from pathlib import Path
from tempfile import mkstemp
from typing import Set

import pytest
from hypothesis import given
from hypothesis.strategies import binary, integers, sampled_from, sets

from modist.package.hasher import DEFAULT_CHUNK_SIZE, HashType, hash_file, hash_io

from ..strategies import pathlib_path

HashType_strategy = sampled_from(HashType).filter(
    lambda hash_type: hash_type != HashType._HashType__available_hashers  # type: ignore
)


@given(
    binary(),
    sets(HashType_strategy),
    integers(min_value=1, max_value=DEFAULT_CHUNK_SIZE),
)
def test_hash_io(content: bytes, hash_types: Set[HashType], chunk_size: int):
    """Ensure hash_io works properly."""

    content_io = BytesIO(content)
    results = hash_io(io=content_io, types=hash_types, chunk_size=chunk_size)
    assert isinstance(results, dict)
    assert len(results) == len(hash_types)

    for hash_type, hash_result in results.items():
        assert isinstance(hash_type, HashType)
        assert isinstance(hash_result, str)

        assert hash_type.hasher(content).hexdigest() == hash_result


@given(
    binary(),
    sets(HashType_strategy),
    integers(min_value=1, max_value=DEFAULT_CHUNK_SIZE),
)
def test_hash_file(content: bytes, hash_types: Set[HashType], chunk_size: int):
    """Ensure hash_file works properly."""

    (_, temp_name) = mkstemp()
    with open(temp_name, "wb") as file_io:
        file_io.write(content)

    try:
        temp_filepath = Path(temp_name).resolve()
        results = hash_file(
            filepath=temp_filepath, types=hash_types, chunk_size=chunk_size
        )
        assert isinstance(results, dict)
        assert len(results) == len(hash_types)

        for hash_type, hash_result in results.items():
            assert isinstance(hash_type, HashType)
            assert isinstance(hash_result, str)

            assert hash_type.hasher(content).hexdigest() == hash_result
    finally:
        os.remove(temp_name)


@given(
    pathlib_path(),
    sets(HashType_strategy),
    integers(min_value=1, max_value=DEFAULT_CHUNK_SIZE),
)
def test_hash_file_raises_FileNotFoundError_with_missing_file(
    filepath: Path, hash_types: Set[HashType], chunk_size: int
):
    """Ensure hash_file raises FileNotFoundError if given a non-existent filepath."""

    with pytest.raises(FileNotFoundError):
        hash_file(filepath=filepath, types=hash_types, chunk_size=chunk_size)
