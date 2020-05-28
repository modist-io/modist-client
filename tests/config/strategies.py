# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""Contains custom hypothesis strategies for manifest configuration testing."""

from datetime import datetime
from typing import Dict, Optional

from hypothesis.strategies import (
    SearchStrategy,
    composite,
    datetimes,
    dictionaries,
    integers,
    just,
)

from modist.config.manifest import MANIFEST_VERSION_MAX, MANIFEST_VERSION_MIN
from modist.package.hasher import HashType

from ..package.strategies import hash_hexdigest, hash_type
from ..strategies import pythonic_name


@composite
def manifest_artifacts(
    draw,
    name_strategy: Optional[SearchStrategy[str]] = None,
    checksum_strategy: Optional[SearchStrategy[str]] = None,
) -> Dict[str, str]:
    """Composite strategy for building a manifest's artifacts dictionary."""

    return draw(
        dictionaries(
            keys=(pythonic_name() if not name_strategy else name_strategy),
            values=(hash_hexdigest() if not checksum_strategy else checksum_strategy),
            min_size=1,
        )
    )


@composite
def minimal_manifest_config_payload(
    draw,
    hash_type_strategy: Optional[SearchStrategy[HashType]] = None,
    artifacts_strategy: Optional[SearchStrategy[Dict[str, str]]] = None,
    built_at_strategy: Optional[SearchStrategy[datetime]] = None,
    version_strategy: Optional[SearchStrategy[int]] = None,
) -> dict:
    """Composite strategy for building a minimal manifest config payload."""

    checksum_type = draw(hash_type() if not hash_type_strategy else hash_type_strategy)
    return {
        "artifacts": draw(
            manifest_artifacts(
                checksum_strategy=hash_hexdigest(hash_type_strategy=just(checksum_type))
            )
            if not artifacts_strategy
            else artifacts_strategy
        ),
        "hash_type": checksum_type,
        "built_at": draw(datetimes() if not built_at_strategy else built_at_strategy),
        "version": draw(
            integers(min_value=MANIFEST_VERSION_MIN, max_value=MANIFEST_VERSION_MAX)
            if not version_strategy
            else version_strategy
        ),
    }
