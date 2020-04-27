# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""Contains the mod-section of the mod configuration."""

from pydantic import BaseModel
from pydantic.fields import Field


MOD_CONFIG_NAME_MIN_LENGTH = 3
MOD_CONFIG_NAME_MAX_LENGTH = 64
MOD_CONFIG_NAME_PATTERN = r"\A[a-zA-Z][\w\-]{2,62}[a-zA-Z0-9]\Z"


class ModConfig(BaseModel):
    """Defines the structure of the base mod config."""

    name: str = Field(
        min_length=MOD_CONFIG_NAME_MIN_LENGTH,
        max_length=MOD_CONFIG_NAME_MAX_LENGTH,
        regex=MOD_CONFIG_NAME_PATTERN,
    )
