# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""Contains unit-tests for the custom config field types."""

import re
from typing import Any, Type

import pytest
from hypothesis import assume, given
from hypothesis.strategies import just, text
from pydantic import BaseModel, ValidationError
from semantic_version import SimpleSpec, Version, validate

from modist.config._types import SemanticSpec, SemanticVersion

from ..strategies import builtins, pydantic_model, semver_spec, semver_version


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


@given(builtins(exclude=[str]))
def test_SemanticVersion_validate_requires_strings(value: Any):
    with pytest.raises(TypeError):
        SemanticVersion.validate(value)


@given(text())
def test_SemanticVersion_validate_requires_valid_semver_string(value: str):
    assume(not validate(value))
    with pytest.raises(ValueError):
        SemanticVersion.validate(value)


@given(
    pydantic_model(fields_strategy=just({"spec": (SemanticSpec, ...)})), semver_spec()
)
def test_SemanticSpec_valid(model: Type[BaseModel], semver_spec: str):
    instance = model(spec=semver_spec)
    assert isinstance(instance.spec, SimpleSpec)  # type: ignore


@given(pydantic_model(fields_strategy=just({"spec": (SemanticSpec, ...)})))
def test_SemanticSpec_generates_valid_schema(model: Type[BaseModel]):
    schema = model.schema()
    assert "properties" in schema
    assert "spec" in schema["properties"]

    spec_schema = schema["properties"]["spec"]
    assert "type" in spec_schema
    assert spec_schema["type"] == "string"
    assert "examples" in spec_schema
    assert len(spec_schema["examples"]) > 0


@given(
    pydantic_model(fields_strategy=just({"spec": (SemanticSpec, ...)})),
    builtins(exclude=[str]),
)
def test_SemanticSpec_only_accepts_strings(model: Type[BaseModel], value: Any):
    with pytest.raises(ValidationError):
        model(spec=value)


@given(builtins(exclude=[str]))
def test_SemanticSpec_validate(value: Any):
    with pytest.raises(TypeError):
        SemanticSpec.validate(value)
