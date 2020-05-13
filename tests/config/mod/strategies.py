# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""Contains custom hypothesis strategies for mod configuration testing."""

from typing import List, Optional

from hypothesis.provisional import urls
from hypothesis.strategies import (
    SearchStrategy,
    characters,
    composite,
    dictionaries,
    from_regex,
    integers,
    lists,
    none,
    nothing,
    one_of,
    sampled_from,
    text,
)

from modist.config.mod.meta import SPEC_VERSION_MAX, SPEC_VERSION_MIN
from modist.config.mod.mod import (
    MOD_AUTHOR_MAX_LENGTH,
    MOD_CATEGORIES_MAX_LENGTH,
    MOD_CATEGORY_PATTERN,
    MOD_CONTRIBUTOR_MAX_LENGTH,
    MOD_DESCRIPTION_MAX_LENGTH,
    MOD_DESCRIPTION_MIN_LENGTH,
    MOD_HOST_PATTERN,
    MOD_KEYWORD_PATTERN,
    MOD_KEYWORDS_MAX_LENGTH,
    MOD_NAME_PATTERN,
)
from modist.config.mod.require import OperatingSystem, ProcessorArchitecture

from ...strategies import semver_spec, semver_version


@composite
def spec_config_payload(
    draw, version_strategy: Optional[SearchStrategy[int]] = None
) -> dict:
    """Composite strategy for building a spec config payload."""

    return {
        "version": draw(
            integers(min_value=SPEC_VERSION_MIN, max_value=SPEC_VERSION_MAX)
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
def require_host_config_payload(
    draw, version_strategy: Optional[SearchStrategy[str]] = None
) -> dict:
    """Composite strategy for building a host require config payload."""

    return {
        "version": draw(semver_spec() if not version_strategy else version_strategy)
    }


@composite
def require_config_payload(
    draw,
    os_strategy: Optional[SearchStrategy[List[str]]] = None,
    arch_strategy: Optional[SearchStrategy[List[str]]] = None,
    host_strategy: Optional[SearchStrategy[dict]] = None,
) -> dict:
    """Composite strategy for building a require config payload."""

    operating_systems = [_.value for _ in OperatingSystem.__members__.values()]
    processor_architectures = [
        _.value for _ in ProcessorArchitecture.__members__.values()
    ]

    return {
        "os": draw(
            one_of([lists(sampled_from(operating_systems), unique=True), none()])
            if not os_strategy
            else os_strategy
        ),
        "arch": draw(
            one_of([lists(sampled_from(processor_architectures), unique=True), none()])
            if not arch_strategy
            else arch_strategy
        ),
        "host": draw(
            one_of(require_host_config_payload(), none())
            if not host_strategy
            else host_strategy
        ),
    }


@composite
def minimal_mod_config_payload(
    draw,
    name_strategy: Optional[SearchStrategy[str]] = None,
    description_strategy: Optional[SearchStrategy[str]] = None,
    host_strategy: Optional[SearchStrategy[str]] = None,
    version_strategy: Optional[SearchStrategy[str]] = None,
    author_strategy: Optional[SearchStrategy[str]] = None,
) -> dict:
    """Composite strategy for building the minimal mod config payload."""

    return {
        "name": draw(
            from_regex(MOD_NAME_PATTERN) if not name_strategy else name_strategy
        ),
        "description": draw(
            text(
                min_size=MOD_DESCRIPTION_MIN_LENGTH,
                max_size=MOD_DESCRIPTION_MAX_LENGTH,
                alphabet=characters(blacklist_categories=["Cc", "Zl"]),
            )
            if not description_strategy
            else description_strategy
        ),
        "host": draw(
            from_regex(MOD_HOST_PATTERN) if not host_strategy else host_strategy
        ),
        "version": draw(semver_version() if not version_strategy else version_strategy),
        "author": draw(
            text(
                max_size=MOD_AUTHOR_MAX_LENGTH,
                alphabet=characters(blacklist_categories=["Cc", "Zl"]),
            )
            if not author_strategy
            else author_strategy
        ),
    }


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
    include_strategy: Optional[SearchStrategy[List[str]]] = None,
    exclude_strategy: Optional[SearchStrategy[List[str]]] = None,
    homepage_strategy: Optional[SearchStrategy[Optional[str]]] = None,
    meta_strategy: Optional[SearchStrategy[dict]] = None,
    require_strategy: Optional[SearchStrategy[dict]] = None,
    depends_strategy: Optional[SearchStrategy[dict]] = None,
    conflicts_strategy: Optional[SearchStrategy[dict]] = None,
    peers_strategy: Optional[SearchStrategy[dict]] = None,
) -> dict:
    """Composite strategy for building a mod config payload."""

    return {
        "name": (
            draw(from_regex(MOD_NAME_PATTERN))
            if not name_strategy
            else draw(name_strategy)
        ),
        "host": (
            draw(from_regex(MOD_HOST_PATTERN))
            if not host_strategy
            else draw(host_strategy)
        ),
        "description": (
            draw(
                text(
                    min_size=MOD_DESCRIPTION_MIN_LENGTH,
                    max_size=MOD_DESCRIPTION_MAX_LENGTH,
                    alphabet=characters(blacklist_categories=["Cc", "Zl"]),
                )
                if not description_strategy
                else description_strategy
            )
        ),
        "version": draw(semver_version() if not version_strategy else version_strategy),
        "author": draw(
            text(
                max_size=MOD_AUTHOR_MAX_LENGTH,
                alphabet=characters(blacklist_categories=["Cc", "Zl"]),
            )
            if not author_strategy
            else author_strategy
        ),
        "contributors": draw(
            lists(
                text(
                    max_size=MOD_CONTRIBUTOR_MAX_LENGTH,
                    alphabet=characters(blacklist_categories=["Cc", "Zl"]),
                )
            )
            if not contributors_strategy
            else contributors_strategy
        ),
        "keywords": draw(
            lists(
                from_regex(MOD_KEYWORD_PATTERN, fullmatch=True),
                max_size=MOD_KEYWORDS_MAX_LENGTH,
                unique=True,
            )
            if not keywords_strategy
            else keywords_strategy
        ),
        "categories": draw(
            lists(
                from_regex(MOD_CATEGORY_PATTERN, fullmatch=True),
                max_size=MOD_CATEGORIES_MAX_LENGTH,
                unique=True,
            )
            if not categories_strategy
            else categories_strategy
        ),
        "include": draw(
            lists(
                text(
                    alphabet=characters(blacklist_categories=["Po", "M", "Z", "S", "C"])
                )
            )
            if not include_strategy
            else include_strategy
        ),
        "exclude": draw(
            lists(
                text(
                    alphabet=characters(blacklist_categories=["Po", "M", "Z", "S", "C"])
                )
            )
            if not exclude_strategy
            else exclude_strategy
        ),
        "homepage": draw(
            one_of([urls(), none()]) if not homepage_strategy else homepage_strategy
        ),
        "meta": draw(meta_config_payload() if not meta_strategy else meta_strategy),
        "require": draw(
            require_config_payload() if not require_strategy else require_strategy
        ),
        "depends": draw(
            dictionaries(from_regex(MOD_NAME_PATTERN), semver_spec(), min_size=1)
            if not depends_strategy
            else depends_strategy
        ),
        "conflicts": draw(
            dictionaries(from_regex(MOD_NAME_PATTERN), semver_spec(), min_size=1)
            if not depends_strategy
            else depends_strategy
        ),
        "peers": draw(
            one_of(
                dictionaries(from_regex(MOD_NAME_PATTERN), semver_spec(), min_size=1),
                dictionaries(nothing(), nothing(), max_size=0),
            )
            if not depends_strategy
            else depends_strategy
        ),
    }
