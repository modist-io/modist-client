# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""Contains unit-tests for the manifest configuration."""

import pytest
from hypothesis import given
from hypothesis.strategies import dictionaries, integers, nothing
from pydantic.error_wrappers import ValidationError

from modist.config.manifest import (
    MANIFEST_VERSION_MAX,
    MANIFEST_VERSION_MIN,
    ManifestConfig,
)

from .strategies import minimal_manifest_config_payload


@given(minimal_manifest_config_payload())
def test_manifest_valid(payload: dict):
    """Ensure ManifestConfig works as expected."""

    config: ManifestConfig = ManifestConfig(**payload)
    assert isinstance(config, ManifestConfig)


@given(
    minimal_manifest_config_payload(
        artifacts_strategy=dictionaries(keys=nothing(), values=nothing(), max_size=0)
    )
)
def test_manifest_invalid_artifacts_min_size(payload: dict):
    """Ensure ManifestConfig raises a ValidationError with no artifacts provided."""

    with pytest.raises(ValidationError):
        ManifestConfig(**payload)


@pytest.mark.extra
@given(
    minimal_manifest_config_payload(
        version_strategy=integers(max_value=MANIFEST_VERSION_MIN - 1)
    )
)
def test_manifest_invalid_version_min(payload: dict):
    """Ensure ManifestConfig raises ValidationError with too small version."""

    with pytest.raises(ValidationError):
        ManifestConfig(**payload)


@pytest.mark.extra
@given(
    minimal_manifest_config_payload(
        version_strategy=integers(min_value=MANIFEST_VERSION_MAX + 1)
    )
)
def test_manifest_invalid_version_max(payload: dict):
    """Ensure ManifestConfig raises ValidationError with too large version."""

    with pytest.raises(ValidationError):
        ManifestConfig(**payload)
