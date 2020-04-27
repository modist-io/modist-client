# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""Contains custom hypothesis strategies for mod configuration testing."""

from hypothesis.strategies import composite, from_regex, integers

from modist.config.mod.mod import MOD_CONFIG_NAME_PATTERN, ModConfig
from modist.config.mod.meta import SPEC_CONFIG_VERSION_MIN, SPEC_CONFIG_VERSION_MAX


@composite
def spec_config_payload(draw, version_strategy=None) -> dict:
    """Composite strategy for building a spec config payload.

    :param Callable[[SearchStrategy], Any] draw: The function for creating a strategy result
    :param SearchStrategy version_strategy: The strategy to use for building a spec version, defaults to None
    :return: A dictionary payload that can be used to create a :class:`~SpecConfig` instance
    :rtype: dict
    """

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
    """Composite strategy fro buliding a meta config payload.

    :param Callable[[SearchStrategy], Any] draw: The function for creating a strategy result
    :param SearchStrategy spec_strategy: The strategy to use for buliding a spec payload, defaults to None
    :return: A dictionary payload that can be used to create a :class:`~MetaConfig` instance
    :rtype: dict
    """

    return {"spec": draw(spec_config_payload() if not spec_strategy else spec_strategy)}


@composite
def mod_config_payload(draw, name_strategy=None, meta_strategy=None) -> dict:
    """Composite strategy for building a mod config payload.

    :param Callable[[SearchStrategy], Any] draw: The function for creating a strategy result
    :param SerachStrategy name_strategy: The strategy to use for building a mod name, defaults to None
    :param SearchStrategy meta_strategy: The strategy to use for building a meta payload, defaults to None
    :return: A dictionary payload that can be used to create a :class:`~ModConfig` instance
    :rtype: dict
    """

    return {
        "name": (
            draw(from_regex(MOD_CONFIG_NAME_PATTERN))
            if not name_strategy
            else draw(name_strategy)
        ),
        "meta": draw(meta_config_payload() if not meta_strategy else meta_strategy),
    }
