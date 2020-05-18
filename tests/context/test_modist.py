# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""Contains unit-tests for the Modist context features."""

from semantic_version import Version

from modist.__version__ import __author__, __contact__, __version__
from modist.context import modist


def test_get_name():
    """Ensure the call to get_name always returns ``Modist``."""

    return modist.get_name() == "Modist"


def test_get_author():
    """Ensure the call to get_author returns the client's __author__ proeperty."""
    return modist.get_author() == __author__


def test_get_contact():
    """Ensure the call to get_contact returns the client's __contact__ proeperty."""
    return modist.get_contact() == __contact__


def test_get_version():
    """Ensure the call to get_version returns the Version instance of __version__."""

    version = modist.get_version()
    assert isinstance(version, Version)
    assert Version(__version__) == version


def test_ModistContext_default():
    """Ensure the construction of ModistContext doesn't do any unexpected mutation."""

    ctx = modist.ModistContext()

    assert ctx.name == modist.get_name()
    assert ctx.author == modist.get_author()
    assert ctx.contact == modist.get_contact()
    assert ctx.version == modist.get_version()
