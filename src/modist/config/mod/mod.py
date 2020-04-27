# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""
"""

from pydantic.fields import Field
from pydantic.dataclasses import dataclass

MOD_CONFIG_NAME_PATTERN = r"\A[a-zA-Z][\w\-]{2,62}[a-zA-Z0-9]\Z"


@dataclass
class ModConfig(object):
    """Defines the structure of the base mod config."""

    name: str = Field(min_length=3, max_length=64, regex=MOD_CONFIG_NAME_PATTERN)
