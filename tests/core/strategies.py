# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""Contains custom hypothesis strategies for core testing."""

from pathlib import Path
from typing import Optional

from hypothesis.strategies import SearchStrategy, composite

from modist.config.mod.mod import ModConfig
from modist.core.mod import Mod

from ..config.mod.strategies import minimal_mod_config
from ..strategies import pathlib_path


@composite
def mod(
    draw,
    config_strategy: Optional[SearchStrategy[ModConfig]] = None,
    path_strategy: Optional[SearchStrategy[Path]] = None,
) -> Mod:
    """Composite strategy for building a sample mod instance."""

    return Mod(
        config=draw(minimal_mod_config() if not config_strategy else config_strategy),
        path=draw(pathlib_path() if not path_strategy else path_strategy),
    )
