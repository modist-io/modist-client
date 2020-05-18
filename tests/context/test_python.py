# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""Contains unit-tests for the Python context features."""

from pathlib import Path
from unittest.mock import patch

from hypothesis import assume, given
from hypothesis.strategies import sampled_from, text
from semantic_version import Version

from modist.context import python

from ..strategies import semver_version

AVAILABLE_IMPLEMENTATIONS = ["IronPython", "CPython", "Jython", "PyPy"]


@given(sampled_from(AVAILABLE_IMPLEMENTATIONS))
def test_get_implementation(implementation_value: str):
    """Ensure call to get_implementation returns the correct PythonImplementation."""

    with patch.object(python, "python_implementation") as mocked_python_implementation:
        mocked_python_implementation.return_value = implementation_value

        implementation = python.get_implementation()
        assert isinstance(implementation, python.PythonImplementation)
        assert (
            python.PythonImplementation(implementation_value.lower()) == implementation
        )


@given(text())
def test_get_implementation_returns_None(implementation_value: str):
    """Ensure call to get_implementation will return None if necessary."""

    assume(implementation_value not in AVAILABLE_IMPLEMENTATIONS)

    with patch.object(python, "python_implementation") as mocked_python_implementation:
        mocked_python_implementation.return_value = implementation_value
        assert python.get_implementation() is None


@given(semver_version())
def test_get_version(version_value: str):
    """Ensure call to get_version return return the appropriate Python version."""

    with patch.object(python, "python_version") as mocked_python_version:
        mocked_python_version.return_value = version_value

        version = python.get_version()
        assert isinstance(version, Version)
        assert Version.coerce(version_value) == version


def test_get_path():
    """Ensure call to get_path returns the appropriate Python path."""

    # As it is notoriously difficult to determine the current path of the current Python
    # runtime, we are going to just assume that :mod:`pythonfinder` has appropraite
    # testing and we only care that we get back a valid :class:`pathlib.Path` instance
    assert isinstance(python.get_path(), Path)


def test_get_path_returns_None():
    """Ensure call to get_path returns None if necessary."""

    with patch.object(python.PythonFinder, "which") as mocked_which:
        mocked_which.return_value = None

        assert python.get_path() is None


def test_PythonContext_default():
    """Ensure the construction of PythonContext doesn't do any unexpected mutation."""

    ctx = python.PythonContext()

    assert ctx.path == python.get_path()
    assert ctx.implementation == python.get_implementation()
    assert ctx.version == python.get_version()
