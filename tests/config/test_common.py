# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""
"""

import json
from typing import Type

import tomlkit as toml
from hypothesis import given

from modist.config._common import BaseConfig

from ..strategies import pydantic_model


@given(pydantic_model(base_class=BaseConfig))
def test_BaseConfig_to_json(config: Type[BaseConfig]):
    instance = config()
    assert hasattr(instance, "to_json")
    content = instance.to_json()
    assert isinstance(content, str)
    assert isinstance(json.loads(content), dict)


@given(pydantic_model(base_class=BaseConfig))
def test_BaseConfig_from_json(config: Type[BaseConfig]):
    assert hasattr(config, "from_json")
    initial_instance = config()
    content = initial_instance.to_json()

    instance = config.from_json(content)
    assert isinstance(instance, config)
    assert instance == initial_instance


@given(pydantic_model(base_class=BaseConfig))
def test_BaseConfig_to_toml(config: Type[BaseConfig]):
    instance = config()
    assert hasattr(instance, "to_toml")
    content = instance.to_toml()
    assert isinstance(content, str)
    assert isinstance(toml.loads(content), dict)


@given(pydantic_model(base_class=BaseConfig))
def test_BaseConfig_from_toml(config: Type[BaseConfig]):
    assert hasattr(config, "from_toml")
    initial_instance = config()
    content = initial_instance.to_toml()

    instance = config.from_toml(content)
    assert isinstance(instance, config)
    assert instance == initial_instance
