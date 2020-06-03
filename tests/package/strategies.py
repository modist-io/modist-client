# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""Contains custom hypothesis strategies for packaging testing."""


from io import BytesIO
from typing import Optional

from hypothesis.strategies import SearchStrategy, binary, composite, sampled_from

from modist.package.hasher import HashType, hash_io

HashType_strategy = sampled_from(HashType).filter(
    lambda hash_type: hash_type != HashType._HashType__available_hashers  # type: ignore
)


@composite
def hash_type(
    draw, hash_type_strategy: Optional[SearchStrategy[HashType]] = None
) -> HashType:
    """Composite strategy for fetching a :class:`~modist.package.hasher.HashType`."""

    return draw(HashType_strategy if not hash_type_strategy else hash_type_strategy)


@composite
def hash_hexdigest(
    draw,
    hash_type_strategy: Optional[SearchStrategy[HashType]] = None,
    content_strategy: Optional[SearchStrategy[bytes]] = None,
) -> str:
    """Composite strategy for building a hash hexdigest."""

    type_ = draw(hash_type(hash_type_strategy=hash_type_strategy))
    content = BytesIO(
        draw(binary(min_size=1) if not content_strategy else content_strategy)
    )
    return hash_io(content, {type_})[type_]
