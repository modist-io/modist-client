# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""Contains strategies that are useful throughout all the module tests."""

from typing import Optional

from hypothesis import assume
from hypothesis.strategies import (
    SearchStrategy,
    text,
    emails,
    booleans,
    integers,
    composite,
    characters,
    from_regex,
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
