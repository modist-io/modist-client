# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""Contains custom hypothesis strategies for mod configuration testing."""

from hypothesis.strategies import composite, from_regex, integers, text, characters

from modist.config.mod.mod import (
    MOD_CONFIG_NAME_PATTERN,
    MOD_CONFIG_HOST_PATTERN,
    MOD_CONFIG_DESCRIPTION_MIN_LENGTH,
    MOD_CONFIG_DESCRIPTION_MAX_LENGTH,
    ModConfig,
)
from modist.config.mod.meta import SPEC_CONFIG_VERSION_MIN, SPEC_CONFIG_VERSION_MAX


@composite
def spec_config_payload(draw, version_strategy=None) -> dict:
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
def meta_config_payload(draw, spec_strategy=None) -> dict:
    """Composite strategy for buliding a meta config payload."""

    return {"spec": draw(spec_config_payload() if not spec_strategy else spec_strategy)}


@composite
def mod_config_payload(
    draw,
    name_strategy=None,
    description_strategy=None,
    host_strategy=None,
    meta_strategy=None,
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
        "meta": draw(meta_config_payload() if not meta_strategy else meta_strategy),
    }
