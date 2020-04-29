# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""Contains the root mod section of the mod configuration."""

from typing import List

from semver import VersionInfo
from pydantic import Field, BaseModel, NameEmail, validator

from .meta import MetaConfig

MOD_CONFIG_NAME_MIN_LENGTH = 3
MOD_CONFIG_NAME_MAX_LENGTH = 64
MOD_CONFIG_NAME_PATTERN = r"\A(?P<name>[a-zA-Z][\w\-]{2,62}[a-zA-Z0-9])\Z"
MOD_CONFIG_HOST_PATTERN = (
    r"\A(?P<publisher>[a-z][a-z0-9\-]{1,62}[a-z0-9])"
    r"\."
    r"(?P<host>[a-z][a-z0-9\-]{1,62}[a-z0-9])\Z"
)
MOD_CONFIG_DESCRIPTION_MIN_LENGTH = 3
MOD_CONFIG_DESCRIPTION_MAX_LENGTH = 240
MOD_CONFIG_DEFAULT_VERSION = "0.0.1"
MOD_CONFIG_KEYWORDS_MAX_LENGTH = 5


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
    host: str = Field(
        title="Mod Host",
        description="Describes the host that the mod is built for",
        regex=MOD_CONFIG_HOST_PATTERN,
    )
    description: str = Field(
        title="Mod Description",
        description="Describes in a short one-liner the purpose of the mod",
        min_length=MOD_CONFIG_DESCRIPTION_MIN_LENGTH,
        max_length=MOD_CONFIG_DESCRIPTION_MAX_LENGTH,
    )
    version: str = Field(
        default=MOD_CONFIG_DEFAULT_VERSION,
        title="Mod Version",
        description="Contains the local mod's version information",
    )
    author: NameEmail = Field(
        title="Mod Author",
        description="Describes the author of the mod and a way of contact",
    )
    contributors: List[NameEmail] = Field(
        default=[],
        title="Mod Contributors",
        description="Describes any contributors to the mod and a way of contact",
    )
    keywords: List[str] = Field(
        default=[],
        title="Mod Keywords",
        description="Tags the mod with specific keywords",
        max_items=MOD_CONFIG_KEYWORDS_MAX_LENGTH,
    )
    meta: MetaConfig = Field(
        title="Meta",
        description="Metadata of the mod configuration format",
        default_factory=MetaConfig,
    )

    @validator("description")
    def validate_description(cls, value: str) -> str:  # noqa
        """Validate the given description.

        :param str value: The given description
        :raises ValueError: When the description contains newlines
        :returns: The validated description
        :rtype: str
        """

        if value.count("\n") > 0:
            raise ValueError("should not have newlines")

        return value

    @validator("version")
    def validate_version(cls, value: str) -> str:  # noqa
        """Validate the given version number.

        :param str value: The given version number
        :raises ValueError: When the given version number is not valid semver
        :return: The validated version number
        :rtype: str
        """

        # NOTE: VersionInfo.parse will raise a ValueError on invalid semver strings
        VersionInfo.parse(value)
        return value
