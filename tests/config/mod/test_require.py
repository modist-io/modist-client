# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""Contains unit-test for the mod configuration require section."""

import pytest
from pydantic import ValidationError
from hypothesis import given, assume
from hypothesis.strategies import text, lists

from modist.config.mod.require import (
    RequireConfig,
    OperatingSystem,
    ProcessorArchitecture,
)

from .strategies import require_config_payload


@given(require_config_payload())
def test_require_valid(payload: dict):
    config = RequireConfig(**payload)
    assert isinstance(config, RequireConfig)


@pytest.mark.extra
@given(require_config_payload(os_strategy=lists(text(), min_size=1)))
def test_require_invalid_os(payload: dict):
    for os_name in payload["os"]:
        try:
            OperatingSystem(os_name)
            assume(False)
        except ValueError:
            break

    with pytest.raises(ValidationError):
        RequireConfig(**payload)


@pytest.mark.extra
@given(require_config_payload(arch_strategy=lists(text(), min_size=1)))
def test_require_invalid_arch(payload: dict):
    for arch_name in payload["arch"]:
        try:
            ProcessorArchitecture(arch_name)
            assume(False)
        except ValueError:
            break

    with pytest.raises(ValidationError):
        RequireConfig(**payload)
