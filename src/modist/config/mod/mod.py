# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""Contains the root mod section of the mod configuration."""

from typing import Dict, List, Optional

from pydantic import Field, HttpUrl, NameEmail, validator

from .._common import BaseConfig
from .._types import SemanticSpec, SemanticVersion
from .meta import MetaConfig
from .require import RequireConfig

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
MOD_CONFIG_KEYWORD_MIN_LENGTH = 3
MOD_CONFIG_KEYWORD_PATTERN = r"\A[^\s]{3,}\Z"
MOD_CONFIG_CATEGORIES_MAX_LENGTH = 5
MOD_CONFIG_CATEGORY_MIN_LENGTH = 3
MOD_CONFIG_CATEGORY_PATTERN = r"\A[^\s]{3,}\Z"


class ModConfig(BaseConfig):
    """Defines the structure of the base mod config."""

    name: str = Field(
        ...,
        title="Mod Name",
        description="Describes the user-given slug identifying name of the mod",
        min_length=MOD_CONFIG_NAME_MIN_LENGTH,
        max_length=MOD_CONFIG_NAME_MAX_LENGTH,
        regex=MOD_CONFIG_NAME_PATTERN,
    )
    host: str = Field(
        ...,
        title="Mod Host",
        description="Describes the host that the mod is built for",
        regex=MOD_CONFIG_HOST_PATTERN,
    )
    description: str = Field(
        ...,
        title="Mod Description",
        description="Describes in a short one-liner the purpose of the mod",
        min_length=MOD_CONFIG_DESCRIPTION_MIN_LENGTH,
        max_length=MOD_CONFIG_DESCRIPTION_MAX_LENGTH,
    )
    version: SemanticVersion = Field(
        ...,
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
        min_length=MOD_CONFIG_KEYWORD_MIN_LENGTH,
        regex=MOD_CONFIG_KEYWORD_PATTERN,
    )
    categories: List[str] = Field(
        default=[],
        title="Mod Categories",
        description="Categorizes the mod with defined categories",
        max_items=MOD_CONFIG_CATEGORIES_MAX_LENGTH,
        min_length=MOD_CONFIG_CATEGORY_MIN_LENGTH,
        regex=MOD_CONFIG_CATEGORY_PATTERN,
    )
    include: List[str] = Field(
        default=[],
        title="Mod Includes",
        description="Describes patterns for files that should be bundled in the mod",
    )
    exclude: List[str] = Field(
        default=[],
        title="Mod Excludes",
        description="Describes patterns for files that shouldn't be bundled in the mod",
    )
    homepage: Optional[HttpUrl] = Field(
        default=None,
        title="Mod Homepage",
        description="Describes an external homepage for the mod",
    )
    meta: MetaConfig = Field(
        title="Meta",
        description="Metadata of the mod configuration format",
        default_factory=MetaConfig,
    )
    require: RequireConfig = Field(
        title="Mod Requirements",
        description="Requirements for the mod",
        default_factory=RequireConfig,
    )
    depends: Dict[str, SemanticSpec] = Field(
        default={},
        title="Mod Dependencies",
        description="Necessary mod dependencies for the mod",
    )
    conflicts: Dict[str, SemanticSpec] = Field(
        default={},
        title="Mod Conflits",
        description="Known conflicting mods of the mod",
    )
    peers: Dict[str, SemanticSpec] = Field(
        default={},
        title="Mod Peers",
        description="Suggested mods that are either enhanced by or enhance the mod",
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

    @validator("keywords")
    def validate_keywords(cls, value: List[str]) -> List[str]:  # noqa
        """Validate the given keywords.

        :param List[str] value: The list of keywords
        :raises ValueError: When there are duplicates in the given list of keywords
        :return: The validated list of keywords
        :rtype: List[str]
        """

        if len(set(value)) != len(value):
            raise ValueError("should not have duplicates")

        return value

    @validator("categories")
    def validate_categories(cls, value: List[str]) -> List[str]:  # noqa
        """Validate the given categories.

        :param List[str] value: The list of categories
        :raises ValueError: When there are duplicates in the list of categories
        :return: The validated list of categories
        :rtype: List[str]
        """

        # NOTE: purposeful duplication of validation logic from keywords as this will
        # later be expanded for validating the categories against the targeted indexing
        # service's supplied categories
        if len(set(value)) != len(value):
            raise ValueError("should not have duplicates")

        return value
