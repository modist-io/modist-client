# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""Contains strategies that are useful throughout all the module tests."""

from typing import Optional

from hypothesis.strategies import (
    SearchStrategy,
    booleans,
    integers,
    composite,
    from_regex,
)


@composite
def semver_version(
    draw,
    major_strategy: SearchStrategy[str] = None,
    minor_strategy: SearchStrategy[str] = None,
    patch_strategy: SearchStrategy[str] = None,
    prerelease_strategy: SearchStrategy[str] = None,
    build_strategy: SearchStrategy[str] = None,
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
