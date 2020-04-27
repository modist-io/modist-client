# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""Contains the root mod section of the mod configuration."""

from pydantic import BaseModel
from pydantic.fields import Field

from .meta import MetaConfig

MOD_CONFIG_NAME_MIN_LENGTH = 3
MOD_CONFIG_NAME_MAX_LENGTH = 64
MOD_CONFIG_NAME_PATTERN = r"\A[a-zA-Z][\w\-]{2,62}[a-zA-Z0-9]\Z"


class ModConfig(BaseModel):
    """Defines the structure of the base mod config."""

    class Config:
        """Configuration for the mod config schema."""

        title = "Mod"

    name: str = Field(
        title="Mod Name",
        description="Describes the user-given slug identifying name of the mod",
        min_length=MOD_CONFIG_NAME_MIN_LENGTH,
        max_length=MOD_CONFIG_NAME_MAX_LENGTH,
        regex=MOD_CONFIG_NAME_PATTERN,
    )
    meta: MetaConfig = Field(
        title="Meta",
        description="Metadata of the mod configuration format",
        default_factory=MetaConfig,
    )
