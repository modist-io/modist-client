# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""
"""

import pytest
from pydantic import ValidationError
from hypothesis import given
from hypothesis.strategies import integers

from modist.config.mod.meta import (
    SPEC_CONFIG_VERSION_MAX,
    SPEC_CONFIG_VERSION_MIN,
    MetaConfig,
    SpecConfig,
)

from .strategies import meta_config_payload, spec_config_payload


@given(meta_config_payload())
def test_meta_valid(payload: dict):
    config = MetaConfig(**payload)
    assert isinstance(config, MetaConfig)


@given(spec_config_payload())
def test_spec_valid(payload: dict):
    config = SpecConfig(**payload)
    assert isinstance(config, SpecConfig)


@pytest.mark.extra
@given(
    spec_config_payload(
        version_strategy=integers(max_value=SPEC_CONFIG_VERSION_MIN - 1)
    )
)
def test_spec_invalid_version_min(payload: dict):
    with pytest.raises(ValidationError):
        SpecConfig(**payload)


@pytest.mark.extra
@given(
    spec_config_payload(
        version_strategy=integers(min_value=SPEC_CONFIG_VERSION_MAX + 1)
    )
)
def test_spec_invalid_version_max(payload: dict):
    with pytest.raises(ValidationError):
        SpecConfig(**payload)
