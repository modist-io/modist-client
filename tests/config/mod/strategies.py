# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""Contains custom hypothesis strategies for mod configuration testing."""

from hypothesis.strategies import composite, from_regex

from modist.config.mod.mod import MOD_CONFIG_NAME_PATTERN, ModConfig


@composite
def mod_config_payload(draw, name_strategy=None) -> dict:
    """Composite strategy for building a mod config payload.

    :param Callable[[SearchStrategy], Any] draw: The function for creating a strategy result
    :param SerachStrategy name_strategy: The strategy to use for building a mod name, defaults to None
    :return: A dictionary payload that can be used to create a :class:`~ModConfig` instance
    :rtype: dict
    """

    return {
        "name": (
            draw(from_regex(MOD_CONFIG_NAME_PATTERN))
            if not name_strategy
            else draw(name_strategy)
        )
    }


@composite
def mod_config(draw, name_strategy=None) -> ModConfig:
    """Composite strategy for building a mod config instance.

    :param Callabe[[SearchStrategy], Any] draw: The function for creating a strategy result
    :param name_strategy:  The strategy to use for building a mod name, defaults to None
    :return: A :class:`~ModConfig` instance
    :rtype: ModConfig
    """

    payload = draw(mod_config_payload(name_strategy=name_strategy))
    return ModConfig(**payload)  # type: ignore
