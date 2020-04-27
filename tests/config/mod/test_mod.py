# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""Contains unit-tests for the mod configuration."""

import re
import random

import pytest
from hypothesis import given, assume
from hypothesis.strategies import text, characters
from pydantic.error_wrappers import ValidationError
from semver import VersionInfo

from modist.config.mod.mod import (
    MOD_CONFIG_HOST_PATTERN,
    MOD_CONFIG_NAME_PATTERN,
    MOD_CONFIG_NAME_MAX_LENGTH,
    MOD_CONFIG_NAME_MIN_LENGTH,
    MOD_CONFIG_DESCRIPTION_MIN_LENGTH,
    MOD_CONFIG_DESCRIPTION_MAX_LENGTH,
    ModConfig,
)

from .strategies import mod_config_payload


@given(mod_config_payload())
def test_config_valid(payload: dict):
    config = ModConfig(**payload)
    assert isinstance(config, ModConfig)


@given(mod_config_payload(name_strategy=text()))
def test_config_invalid_name(payload: dict):
    assume(not re.match(MOD_CONFIG_NAME_PATTERN, payload["name"]))
    with pytest.raises(ValidationError):
        ModConfig(**payload)


@given(mod_config_payload(name_strategy=text(max_size=MOD_CONFIG_NAME_MIN_LENGTH - 1)))
def test_config_invalid_name_min_length(payload: dict):
    with pytest.raises(ValidationError):
        ModConfig(**payload)


@given(mod_config_payload(name_strategy=text(min_size=MOD_CONFIG_NAME_MAX_LENGTH + 1)))
def test_config_invalid_name_max_length(payload: dict):
    with pytest.raises(ValidationError):
        ModConfig(**payload)


@given(mod_config_payload(host_strategy=text()))
def test_config_invalid_host(payload: dict):
    assume(not re.match(MOD_CONFIG_HOST_PATTERN, payload["host"]))
    with pytest.raises(ValidationError):
        ModConfig(**payload)


@given(mod_config_payload(description_strategy=text()))
def test_config_invalid_description_with_newline(payload: dict):
    description = payload["description"]
    index = random.randint(0, len(description))
    payload["description"] = description[:index] + "\n" + description[:index]

    with pytest.raises(ValidationError):
        ModConfig(**payload)


@given(
    mod_config_payload(
        description_strategy=text(
            max_size=MOD_CONFIG_DESCRIPTION_MIN_LENGTH - 1,
            alphabet=characters(blacklist_categories=["Cc", "Zl"]),
        )
    )
)
def test_config_invalid_description_min_length(payload: dict):
    with pytest.raises(ValidationError):
        ModConfig(**payload)


@given(
    mod_config_payload(
        description_strategy=text(
            min_size=MOD_CONFIG_DESCRIPTION_MAX_LENGTH + 1,
            max_size=(
                MOD_CONFIG_DESCRIPTION_MAX_LENGTH + 2
            ),  # NOTE: we only really care about violating the max length validator
            alphabet=characters(blacklist_categories=["Cc", "Zl"]),
        )
    )
)
def test_config_invalid_description_max_length(payload: dict):
    with pytest.raises(ValidationError):
        ModConfig(**payload)


@given(mod_config_payload(version_strategy=text()))
def test_config_invalid_version(payload: dict):
    with pytest.raises(ValidationError):
        ModConfig(**payload)
