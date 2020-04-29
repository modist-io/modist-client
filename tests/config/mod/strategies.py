# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""Contains custom hypothesis strategies for mod configuration testing."""

from typing import List, Optional

from hypothesis.strategies import (
    SearchStrategy,
    text,
    lists,
    integers,
    composite,
    characters,
    from_regex,
)

from modist.config.mod.mod import (
    MOD_CONFIG_HOST_PATTERN,
    MOD_CONFIG_NAME_PATTERN,
    MOD_CONFIG_KEYWORD_PATTERN,
    MOD_CONFIG_CATEGORY_PATTERN,
    MOD_CONFIG_KEYWORDS_MAX_LENGTH,
    MOD_CONFIG_CATEGORIES_MAX_LENGTH,
    MOD_CONFIG_DESCRIPTION_MAX_LENGTH,
    MOD_CONFIG_DESCRIPTION_MIN_LENGTH,
)
from modist.config.mod.meta import SPEC_CONFIG_VERSION_MAX, SPEC_CONFIG_VERSION_MIN

from ...strategies import name_email, semver_version


@composite
def spec_config_payload(
    draw, version_strategy: Optional[SearchStrategy[int]] = None
) -> dict:
    """Composite strategy for building a spec config payload."""

    return {
        "version": draw(
            integers(
                min_value=SPEC_CONFIG_VERSION_MIN, max_value=SPEC_CONFIG_VERSION_MAX
            )
        )
        if not version_strategy
        else draw(version_strategy)
    }


@composite
def meta_config_payload(
    draw, spec_strategy: Optional[SearchStrategy[dict]] = None
) -> dict:
    """Composite strategy for buliding a meta config payload."""

    return {"spec": draw(spec_config_payload() if not spec_strategy else spec_strategy)}


@composite
def mod_config_payload(
    draw,
    name_strategy: Optional[SearchStrategy[str]] = None,
    description_strategy: Optional[SearchStrategy[str]] = None,
    host_strategy: Optional[SearchStrategy[str]] = None,
    version_strategy: Optional[SearchStrategy[str]] = None,
    author_strategy: Optional[SearchStrategy[str]] = None,
    contributors_strategy: Optional[SearchStrategy[List[str]]] = None,
    keywords_strategy: Optional[SearchStrategy[List[str]]] = None,
    categories_strategy: Optional[SearchStrategy[List[str]]] = None,
    meta_strategy: Optional[SearchStrategy[dict]] = None,
) -> dict:
    """Composite strategy for building a mod config payload."""

    return {
        "name": (
            draw(from_regex(MOD_CONFIG_NAME_PATTERN))
            if not name_strategy
            else draw(name_strategy)
        ),
        "host": (
            draw(from_regex(MOD_CONFIG_HOST_PATTERN))
            if not host_strategy
            else draw(host_strategy)
        ),
        "description": (
            draw(
                text(
                    min_size=MOD_CONFIG_DESCRIPTION_MIN_LENGTH,
                    max_size=MOD_CONFIG_DESCRIPTION_MAX_LENGTH,
                    alphabet=characters(blacklist_categories=["Cc", "Zl"]),
                )
                if not description_strategy
                else description_strategy
            )
        ),
        "version": draw(semver_version() if not version_strategy else version_strategy),
        "author": draw(name_email() if not author_strategy else author_strategy),
        "contributors": draw(
            lists(name_email()) if not contributors_strategy else contributors_strategy
        ),
        "keywords": draw(
            lists(
                from_regex(MOD_CONFIG_KEYWORD_PATTERN, fullmatch=True),
                max_size=MOD_CONFIG_KEYWORDS_MAX_LENGTH,
                unique=True,
            )
            if not keywords_strategy
            else keywords_strategy
        ),
        "categories": draw(
            lists(
                from_regex(MOD_CONFIG_CATEGORY_PATTERN, fullmatch=True),
                max_size=MOD_CONFIG_CATEGORIES_MAX_LENGTH,
                unique=True,
            )
            if not categories_strategy
            else categories_strategy
        ),
        "meta": draw(meta_config_payload() if not meta_strategy else meta_strategy),
    }
