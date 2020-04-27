# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""Contains unit-tests for the mod configuration."""

import re

import pytest
from hypothesis import given, assume
from hypothesis.strategies import text
from pydantic.error_wrappers import ValidationError

from modist.config.mod.mod import (
    MOD_CONFIG_HOST_PATTERN,
    MOD_CONFIG_NAME_PATTERN,
    MOD_CONFIG_NAME_MAX_LENGTH,
    MOD_CONFIG_NAME_MIN_LENGTH,
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
