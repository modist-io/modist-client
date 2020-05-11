# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""
"""

import re
from typing import Any, Type

import pytest
from hypothesis import given
from hypothesis.strategies import just
from pydantic import BaseModel, ValidationError
from semantic_version import Version

from modist.config._types import SemanticVersion

from ..strategies import builtins, pydantic_model, semver_version


@given(
    pydantic_model(fields_strategy=just({"version": (SemanticVersion, ...)})),
    semver_version(),
)
def test_SemanticVersion_valid(model: Type[BaseModel], semver_version: str):
    instance = model(version=semver_version)
    assert isinstance(instance.version, Version)  # type: ignore


@given(pydantic_model(fields_strategy=just({"version": (SemanticVersion, ...)})))
def test_SemanticVersion_generates_valid_schema(model: Type[BaseModel]):
    schema = model.schema()
    assert "properties" in schema
    assert "version" in schema["properties"]

    version_schema = schema["properties"]["version"]
    assert "type" in version_schema
    assert version_schema["type"] == "string"
    assert "examples" in version_schema
    assert len(version_schema["examples"]) > 0
    assert "pattern" in version_schema
    assert len(version_schema["pattern"]) > 0
    assert re.compile(version_schema["pattern"])


@given(
    pydantic_model(fields_strategy=just({"version": (SemanticVersion, ...)})),
    builtins(exclude=[str]),
)
def test_SemanticVersion_only_accepts_strings(model: Type[BaseModel], value: Any):
    with pytest.raises(ValidationError):
        model(version=value)
