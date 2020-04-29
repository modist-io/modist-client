# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""Contains strategies that are useful throughout all the module tests."""

from typing import Any, Dict, List, Type, Optional

from pydantic import BaseModel, create_model
from hypothesis import assume
from hypothesis.strategies import (
    SearchStrategy,
    none,
    text,
    binary,
    builds,
    emails,
    floats,
    one_of,
    booleans,
    integers,
    composite,
    characters,
    from_regex,
    dictionaries,
    complex_numbers,
)


@composite
def builtins(
    draw, include: Optional[List[Type]] = None, exclude: Optional[List[Type]] = None
) -> Any:
    """Composite strategy fro building an instance of a builtin type.

    This strategy allows you to check against builtin types for when you need to do
    varaible validation (which should be rare). By default this composite will generate
    all available types of builtins, however you can either tell it to only generate
    some types or exclude some types. You do this using the ``include`` and ``exclude``
    parameters.

    For example using the ``include`` parameter like the following will ONLY generate
    strings and floats for the samples:

    >>> @given(builtins(include=[str, float]))
    ... def test_only_strings_and_floats(value: Union[str, float]):
    ...     assert isinstance(value, (str, float))

    Similarly, you can specify to NOT generate Nones and complex numbers like the
    following example:

    >>> @given(builtins(exclude=[None, complex]))
    ... def test_not_none_or_complex(value: Any):
    ...     assert value and not isinstance(value, complex)
    """

    strategies: Dict[Any, SearchStrategy[Any]] = {
        None: none(),
        int: integers(),
        bool: booleans(),
        float: floats(allow_nan=False),
        tuple: builds(tuple),
        list: builds(list),
        set: builds(set),
        frozenset: builds(frozenset),
        str: text(),
        bytes: binary(),
        complex: complex_numbers(),
    }

    to_use = set(strategies.keys())
    if include and len(include) > 0:
        to_use = set(include)

    if exclude and len(exclude) > 0:
        to_use = to_use - set(exclude)

    return draw(
        one_of([strategy for key, strategy in strategies.items() if key in to_use])
    )


@composite
def pythonic_name(draw, name_strategy: Optional[SearchStrategy[str]] = None) -> str:
    """Composite strategy for building a Python valid variable / class name."""

    return draw(
        from_regex(r"\A[a-zA-Z]+[a-zA-Z0-9\_]*\Z")
        if not name_strategy
        else name_strategy
    )


@composite
def pydantic_model(
    draw,
    name_strategy: Optional[SearchStrategy[str]] = None,
    fields_strategy: Optional[SearchStrategy[Dict[str, Any]]] = None,
) -> Type[BaseModel]:
    """Composite strategy for building a random Pydantic model."""

    return create_model(
        draw(pythonic_name() if not name_strategy else name_strategy),
        **draw(
            dictionaries(pythonic_name(), builtins(exclude=[None, set]),)
            if not fields_strategy
            else fields_strategy
        ),
    )


@composite
def name_email(
    draw,
    name_strategy: Optional[SearchStrategy[str]] = None,
    email_strategy: Optional[SearchStrategy[str]] = None,
    include_name: Optional[bool] = None,
) -> str:
    """Composite strategy for building a named email string."""

    email = draw(emails() if not email_strategy else email_strategy)
    # HACK: hypothesis will sometimes generate emails with `--` in the domain
    # (which isn't technically wrong) but violates many validators
    assume("--" not in email)

    if include_name or draw(booleans()):
        return (
            draw(
                text(alphabet=characters(whitelist_categories=["L"]))
                if not name_strategy
                else name_strategy
            )
            + f" <{email!s}>"
        )

    return email


@composite
def semver_version(
    draw,
    major_strategy: Optional[SearchStrategy[str]] = None,
    minor_strategy: Optional[SearchStrategy[str]] = None,
    patch_strategy: Optional[SearchStrategy[str]] = None,
    prerelease_strategy: Optional[SearchStrategy[str]] = None,
    build_strategy: Optional[SearchStrategy[str]] = None,
    include_prerelesase: Optional[bool] = None,
    include_build: Optional[bool] = None,
) -> str:
    """Composite strategy for building a semver version string."""

    version = ".".join(
        [
            str(draw(integers(min_value=0) if not strategy else strategy))
            for strategy in (major_strategy, minor_strategy, patch_strategy,)
        ]
    )

    if include_prerelesase or draw(booleans()):
        version += "-" + draw(
            from_regex(
                r"\A((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
                r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*)\Z"
            )
            if not prerelease_strategy
            else prerelease_strategy
        )

    if include_build or draw(booleans()):
        version += "+" + draw(
            from_regex(r"\A([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*)\Z")
            if not build_strategy
            else build_strategy
        )

    return version
