# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""
"""

import pytest
from pydantic import ValidationError
from hypothesis import given, assume
from hypothesis.strategies import text, lists

from modist.config.mod.require import RequireConfig, OperatingSystem

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
