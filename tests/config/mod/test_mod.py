# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""Contains unit-tests for the mod configuration."""

import re
import string
from random import Random
from typing import List
from urllib.parse import urlparse

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis.strategies import characters, from_regex, lists, randoms, text
from pydantic import ValidationError
from pydantic.errors import EmailError
from pydantic.networks import validate_email

from modist.config.mod.mod import (
    MOD_CATEGORIES_MAX_LENGTH,
    MOD_CATEGORY_MIN_LENGTH,
    MOD_CATEGORY_PATTERN,
    MOD_DESCRIPTION_MAX_LENGTH,
    MOD_DESCRIPTION_MIN_LENGTH,
    MOD_HOST_PATTERN,
    MOD_KEYWORD_MIN_LENGTH,
    MOD_KEYWORD_PATTERN,
    MOD_KEYWORDS_MAX_LENGTH,
    MOD_NAME_MAX_LENGTH,
    MOD_NAME_MIN_LENGTH,
    MOD_NAME_PATTERN,
    ModConfig,
)

from .strategies import minimal_mod_config_payload


@given(minimal_mod_config_payload())
def test_config_valid(payload: dict):
    """Ensure ModConfig is valid."""

    config = ModConfig(**payload)
    assert isinstance(config, ModConfig)


@pytest.mark.extra
@given(minimal_mod_config_payload(name_strategy=text(max_size=MOD_NAME_MAX_LENGTH)))
def test_config_invalid_name(payload: dict):
    """Ensure ModConfig raises ValidationError on invalid name."""

    assume(not re.match(MOD_NAME_PATTERN, payload["name"]))
    with pytest.raises(ValidationError):
        ModConfig(**payload)


@pytest.mark.extra
@given(minimal_mod_config_payload(name_strategy=text(max_size=MOD_NAME_MIN_LENGTH - 1)))
def test_config_invalid_name_min_length(payload: dict):
    """Ensure ModConfig raises ValidationError on too short name."""

    with pytest.raises(ValidationError):
        ModConfig(**payload)


@pytest.mark.extra
@pytest.mark.expensive
@settings(suppress_health_check=(HealthCheck.too_slow,))
@given(
    minimal_mod_config_payload(
        name_strategy=text(
            min_size=MOD_NAME_MAX_LENGTH + 1, max_size=MOD_NAME_MAX_LENGTH + 1,
        )
    )
)
def test_config_invalid_name_max_length(payload: dict):
    """Ensure ModConfig raises ValidationError on too long name."""

    with pytest.raises(ValidationError):
        ModConfig(**payload)


@pytest.mark.extra
@given(minimal_mod_config_payload(host_strategy=text()))
def test_config_invalid_host(payload: dict):
    """Ensure ModConfig raises ValidationError on invalid host."""

    assume(not re.match(MOD_HOST_PATTERN, payload["host"]))
    with pytest.raises(ValidationError):
        ModConfig(**payload)


@given(
    randoms(),
    minimal_mod_config_payload(
        description_strategy=text(
            max_size=MOD_DESCRIPTION_MAX_LENGTH, min_size=MOD_DESCRIPTION_MIN_LENGTH,
        )
    ),
)
def test_config_invalid_description_with_newline(random: Random, payload: dict):
    """Ensure ModConfig raises ValidationError on description with newlines."""

    description = payload["description"]
    index = random.randint(0, len(description))
    payload["description"] = description[:index] + "\n" + description[index:]
    with pytest.raises(ValidationError):
        ModConfig(**payload)


@given(
    randoms(),
    text(max_size=MOD_DESCRIPTION_MAX_LENGTH, min_size=MOD_DESCRIPTION_MIN_LENGTH,),
)
def test_config_validate_description_raises_ValueError_with_newline(
    random: Random, description: str
):
    """Ensure ModConfig validator raisees ValueError on description with newlines."""

    index = random.randint(0, len(description))
    description = description[:index] + "\n" + description[index:]
    with pytest.raises(ValueError) as excinfo:
        ModConfig.validate_description(description)

    assert "should not have newlines" in str(excinfo.value)


@pytest.mark.extra
@given(
    minimal_mod_config_payload(
        description_strategy=text(
            max_size=MOD_DESCRIPTION_MIN_LENGTH - 1,
            alphabet=characters(blacklist_categories=["Cc", "Zl"]),
        )
    )
)
def test_config_invalid_description_min_length(payload: dict):
    """Ensure ModConfig raises ValidationError on too short description."""

    with pytest.raises(ValidationError):
        ModConfig(**payload)


@pytest.mark.extra
@pytest.mark.expensive
@settings(suppress_health_check=(HealthCheck.too_slow,))
@given(
    minimal_mod_config_payload(
        description_strategy=text(
            min_size=MOD_DESCRIPTION_MAX_LENGTH + 1,
            max_size=MOD_DESCRIPTION_MAX_LENGTH + 1,
            alphabet=characters(blacklist_categories=["Cc", "Zl"]),
        )
    )
)
def test_config_invalid_description_max_length(payload: dict):
    """Ensure ModConfig raises ValidationError on too long description."""

    with pytest.raises(ValidationError):
        ModConfig(**payload)


@given(minimal_mod_config_payload(version_strategy=text()))
def test_config_invalid_version(payload: dict):
    """Ensure ModConfig raises ValidationError on invalid version."""

    with pytest.raises(ValidationError):
        ModConfig(**payload)


@pytest.mark.extra
@given(minimal_mod_config_payload(author_strategy=text()))
def test_config_invalid_author(payload: dict):
    """Ensure ModConfig raises ValidationError on invalid author."""

    try:
        # NOTE: here we are explicitly ensuring that the email
        # (randomly generated by the text() strategy) is invalid
        validate_email(payload["author"])
        assume(False)
    except EmailError:
        pass

    with pytest.raises(ValidationError):
        ModConfig(**payload)


@pytest.mark.extra
@given(
    minimal_mod_config_payload(), lists(text(), min_size=1),
)
def test_config_invalid_contributors(payload: dict, contributors: List[str]):
    """Ensure ModConfig raises ValidationError on invalid contributors."""

    payload["contributors"] = contributors
    for contributor in payload["contributors"]:
        try:
            validate_email(contributor)
            assume(False)
        except EmailError:
            break

    with pytest.raises(ValidationError):
        ModConfig(**payload)


@pytest.mark.extra
@given(
    minimal_mod_config_payload(),
    lists(
        text(alphabet=string.ascii_letters, min_size=MOD_KEYWORD_MIN_LENGTH),
        min_size=MOD_KEYWORDS_MAX_LENGTH + 1,
        unique=True,
    ),
)
def test_config_invalid_keywords_max_size(payload: dict, keywords: List[str]):
    """Ensure ModConfig raises ValidationError on too many keywords."""

    payload["keywords"] = keywords
    with pytest.raises(ValidationError):
        ModConfig(**payload)


@pytest.mark.extra
@given(
    minimal_mod_config_payload(),
    lists(
        text(alphabet=characters(whitelist_categories=["Z"])),
        min_size=1,
        max_size=MOD_KEYWORDS_MAX_LENGTH,
        unique=True,
    ),
)
def test_config_invalid_keywords(payload: dict, keywords: List[str]):
    """Ensure ModConfig raises ValidationError on invalid keywords."""

    payload["keywords"] = keywords
    with pytest.raises(ValidationError):
        ModConfig(**payload)


@given(
    minimal_mod_config_payload(),
    lists(
        from_regex(MOD_KEYWORD_PATTERN, fullmatch=True),
        min_size=1,
        max_size=MOD_KEYWORDS_MAX_LENGTH - 1,
        unique=False,
    ),
)
def test_config_invalid_keywords_duplicates(payload: dict, keywords: List[str]):
    """Ensure ModConfig raises ValidationError on duplicate keywords."""

    payload["keywords"] = keywords
    payload["keywords"].append(payload["keywords"][-1])
    with pytest.raises(ValidationError):
        ModConfig(**payload)


@given(
    lists(
        from_regex(MOD_KEYWORD_PATTERN, fullmatch=True),
        min_size=1,
        max_size=MOD_KEYWORDS_MAX_LENGTH - 1,
        unique=False,
    )
)
def test_config_validate_keywords_raises_ValueError_on_duplicates(keywords: List[str]):
    """Ensure ModConfig validator raises ValueError on duplicate keywords."""

    keywords.append(keywords[-1])
    with pytest.raises(ValueError) as excinfo:
        ModConfig.validate_keywords(keywords)

    assert "should not have duplicates" in str(excinfo.value)


@given(
    lists(
        from_regex(MOD_KEYWORD_PATTERN, fullmatch=True),
        min_size=1,
        max_size=MOD_KEYWORDS_MAX_LENGTH,
        unique=True,
    )
)
def test_config_validate_keywords_returns_keywords(keywords: List[str]):
    """Ensure ModConfig validator returns valid keywords."""

    assert ModConfig.validate_keywords(keywords) == keywords


@pytest.mark.extra
@given(
    minimal_mod_config_payload(),
    lists(
        text(alphabet=string.ascii_letters, min_size=MOD_CATEGORY_MIN_LENGTH),
        min_size=MOD_CATEGORIES_MAX_LENGTH + 1,
        unique=True,
    ),
)
def test_config_invalid_categories_max_size(payload: dict, categories: List[str]):
    """Ensure ModConfig raises ValidationError on too many categories."""

    payload["categories"] = categories
    with pytest.raises(ValidationError):
        ModConfig(**payload)


@pytest.mark.extra
@given(
    minimal_mod_config_payload(),
    lists(
        text(alphabet=characters(whitelist_categories=["Z"])),
        min_size=1,
        max_size=MOD_CATEGORIES_MAX_LENGTH,
        unique=True,
    ),
)
def test_config_invalid_categories(payload: dict, categories: List[str]):
    """Ensure ModConfig raises ValidationError on invalid categories."""

    payload["categories"] = categories
    with pytest.raises(ValidationError):
        ModConfig(**payload)


@given(
    minimal_mod_config_payload(),
    lists(
        from_regex(MOD_CATEGORY_PATTERN, fullmatch=True),
        min_size=1,
        max_size=MOD_CATEGORIES_MAX_LENGTH - 1,
        unique=False,
    ),
)
def test_config_invalid_categories_duplicates(payload: dict, categories: List[str]):
    """Ensure ModConfig raises ValidationError on duplicate categories."""

    payload["categories"] = categories
    payload["categories"].append(payload["categories"][-1])
    with pytest.raises(ValidationError):
        ModConfig(**payload)


@given(
    lists(
        from_regex(MOD_CATEGORY_PATTERN, fullmatch=True),
        min_size=1,
        max_size=MOD_CATEGORIES_MAX_LENGTH - 1,
        unique=False,
    )
)
def test_config_validate_categories_raises_ValueError_on_duplicates(
    categories: List[str],
):
    """Ensure ModConfig validator raises ValueError on duplicate categories."""

    categories.append(categories[-1])
    with pytest.raises(ValueError) as excinfo:
        ModConfig.validate_categories(categories)

    assert "should not have duplicates" in str(excinfo.value)


@given(
    lists(
        from_regex(MOD_CATEGORY_PATTERN, fullmatch=True),
        min_size=1,
        max_size=MOD_CATEGORIES_MAX_LENGTH,
        unique=True,
    )
)
def test_config_validate_categories_returns_categories(categories: List[str]):
    """Ensure ModConfig validator returns valid categories."""

    assert ModConfig.validate_categories(categories) == categories


@pytest.mark.extra
@given(minimal_mod_config_payload(), text())
def test_config_invalid_homepage(payload: dict, homepage: str):
    """Ensure ModConfig raises ValidationError on invalid homepage."""

    payload["homepage"] = homepage
    try:
        # NOTE: because we are utilizing an HttpUrl for the homepage field, the easiest
        # way of ensuring some text violates the homepage validation is to make sure the
        # scheme is not provided
        if len(urlparse(payload["homepage"]).scheme) > 0:
            assume(False)
    except ValueError:
        pass

    with pytest.raises(ValidationError):
        ModConfig(**payload)
