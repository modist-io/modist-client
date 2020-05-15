# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""
"""

from io import IOBase
from pathlib import Path

from ..core.context import instance as ctx

if ctx.system.is_64bit:
    from xxhash import xxh64 as xxhash
else:
    from xxhash import xxh32 as xxhash


def checksum_content(content: bytes) -> str:
    return xxhash(content).hexdigest()


def checksum_io(io: IOBase) -> str:
    pass


def checksum_path(path: Path) -> str:
    pass


def validate_content(content: bytes, checksum: str) -> bool:
    pass
