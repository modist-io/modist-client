# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""Contains a mod's manifest configuration."""

from datetime import datetime
from typing import Dict

from pydantic import Field, validator

from ..package.hasher import HashType
from ._common import BaseConfig

MANIFEST_DEFAULT_VERSION = 1
MANIFEST_VERSION_MIN = 1
MANIFEST_VERSION_MAX = MANIFEST_DEFAULT_VERSION


class ManifestConfig(BaseConfig):
    """Defines the structure of a mod's archive manifest."""

    artifacts: Dict[str, str] = Field(
        ...,
        title="Manifest Artifacts",
        description="Describes the list of artifacts within the archive",
    )
    hash_type: HashType = Field(
        ...,
        title="Manifest Hash Type",
        description="Describes the type of hashing algorithm used to hash artifacts",
    )
    built_at: datetime = Field(
        title="Manifest Build Date",
        description="The datetime the manifest was built",
        default_factory=datetime.now,
    )
    version: int = Field(
        title="Manifest Version",
        description="Describes the manifest version",
        default=MANIFEST_DEFAULT_VERSION,
        ge=MANIFEST_VERSION_MIN,
        le=MANIFEST_VERSION_MAX,
    )

    @validator("artifacts")
    def validate_artifacts(cls, value: Dict[str, str]) -> Dict[str, str]:  # noqa
        """Validate the manifest's provided artifacts.

        :param Dict[str, str] value: The dictionary of name to checksum artifacts
        :raises ValueError: If there are no artifacts present
        :return: The validated dictionary of name to checksum artifacts
        :rtype: Dict[str, str]
        """

        if len(value) <= 0:
            raise ValueError("requires at least one artifact")

        return value
