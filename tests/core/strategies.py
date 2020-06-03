# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""Contains custom hypothesis strategies for core testing."""

from pathlib import Path
from typing import Dict, Optional

from hypothesis.strategies import SearchStrategy, binary, composite, dictionaries

from modist.config.mod.mod import ModConfig
from modist.core.mod import Mod

from ..config.mod.strategies import minimal_mod_config
from ..strategies import pathlib_path


@composite
def fake_mod(
    draw,
    config_strategy: Optional[SearchStrategy[ModConfig]] = None,
    path_strategy: Optional[SearchStrategy[Path]] = None,
) -> Mod:
    """Composite strategy for building a sample mod instance."""

    return Mod(
        config=draw(minimal_mod_config() if not config_strategy else config_strategy),
        path=draw(pathlib_path() if not path_strategy else path_strategy),
    )


@composite
def mod_artifacts(
    draw,
    path_strategy: Optional[SearchStrategy[Path]] = None,
    content_strategy: Optional[SearchStrategy[bytes]] = None,
) -> Dict[Path, bytes]:
    """Composite strategy for building a dictionary of artifact paths and content."""

    return draw(
        dictionaries(
            keys=(pathlib_path() if not path_strategy else path_strategy),
            values=(binary(min_size=1) if not content_strategy else content_strategy),
            min_size=1,
        )
    )


@composite
def real_mod(
    draw,
    parent_dir: Path,
    config_strategy: Optional[SearchStrategy[ModConfig]] = None,
    artifacts_strategy: Optional[SearchStrategy[Dict[Path, bytes]]] = None,
) -> Mod:
    """Composite strategy for building a mod which existing on the file system."""

    if not parent_dir.is_dir():
        raise NotADirectoryError(f"no such directory {parent_dir!r} exists")

    config: ModConfig = draw(
        minimal_mod_config() if not config_strategy else config_strategy
    )
    mod = Mod.create(
        dirpath=parent_dir,
        name=config.name,
        description=config.description,
        host=config.host,
        author=config.author,
    )

    for artifact_path, content in draw(
        mod_artifacts() if not artifacts_strategy else artifacts_strategy
    ).items():
        filepath = parent_dir / artifact_path
        if not filepath.parent.is_dir():
            filepath.parent.mkdir(parents=True)

        with filepath.open("wb") as file_io:
            file_io.write(content)

    return mod
