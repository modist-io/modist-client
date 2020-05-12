# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""Contains unit-test for the mod configuration require section."""

import pytest
from hypothesis import assume, given
from hypothesis.strategies import lists, text
from pydantic import ValidationError

from modist.config.mod.require import (
    HostConfig,
    OperatingSystem,
    ProcessorArchitecture,
    RequireConfig,
)

from .strategies import require_config_payload, require_host_config_payload


@given(require_config_payload())
def test_require_valid(payload: dict):
    """Ensure RequireConfig is valid."""

    config = RequireConfig(**payload)
    assert isinstance(config, RequireConfig)


@pytest.mark.extra
@given(require_config_payload(os_strategy=lists(text(), min_size=1)))
def test_require_invalid_os(payload: dict):
    """Ensure RequireConfig raises ValidationError when using an invalid os name."""

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
    """Ensure RequireConfig raises ValidationError when using an invalid arch name."""

    for arch_name in payload["arch"]:
        try:
            ProcessorArchitecture(arch_name)
            assume(False)
        except ValueError:
            break

    with pytest.raises(ValidationError):
        RequireConfig(**payload)


@given(require_host_config_payload())
def test_require_host_valid(payload: dict):
    """Ensure HostConfig is valid."""

    config = HostConfig(**payload)
    assert isinstance(config, HostConfig)


@pytest.mark.extra
@given(require_host_config_payload(version_strategy=text(min_size=10)))
def test_require_host_invalid_version(payload: dict):
    """Ensure HostConfig raises ValidationError when using an invalid version spec.

    ..note:: Magic-number 10 here is used to help ensure we are not always just
        generating 0 which can all be considered valid SemanticSpec inputs
    """

    with pytest.raises(ValidationError):
        HostConfig(**payload)
