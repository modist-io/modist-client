# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""Contains the meta section of the mod configuration."""

from pydantic import Field

from .._common import BaseConfig

SPEC_CONFIG_DEFAULT_VERSION = 1
SPEC_CONFIG_VERSION_MIN = 1
SPEC_CONFIG_VERSION_MAX = SPEC_CONFIG_DEFAULT_VERSION


class SpecConfig(BaseConfig):
    """Defines the structure of the meta spec config."""

    version: int = Field(
        default=SPEC_CONFIG_DEFAULT_VERSION,
        title="Spec Version",
        description="Describes the mod configuration spec version",
        ge=SPEC_CONFIG_VERSION_MIN,
        le=SPEC_CONFIG_VERSION_MAX,
    )


class MetaConfig(BaseConfig):
    """Defines the structure of the mod meta config."""

    spec: SpecConfig = Field(
        title="Meta Specification",
        description="Specifications for the mod configuration format",
        default_factory=SpecConfig,
    )
