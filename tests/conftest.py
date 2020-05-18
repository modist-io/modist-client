# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""Contains pytest configuration and features for the module tests."""

import copy
import os
import shutil
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Generator


@contextmanager
def os_environ(update_dict: Dict[str, Any]) -> Generator[os._Environ, None, None]:
    """Context manager to wrap and temporarily update the os environment.

    :param Dict[str, Any] update_dict: The keys and values to update the current os
        environment dictionary with
    """

    orig_environment = copy.copy(os.environ)
    try:
        os.environ.update(update_dict)
        yield os.environ
    finally:
        os.environ = orig_environment


@contextmanager
def cd(path: Path, create_missing: bool = True) -> Generator[Path, None, None]:
    """Context manager to ``cd`` into a given directory.

    If the path doesn't exist and ``create_missing`` is set to ``True``, this context
    manager will create the path as a directory with mode ``0o777`` and clean up the
    directory once the context is exited.

    :param Path path: The path of the directory to change to
    :param bool create_missing: If True, the given path will be created as a directory
        if one doesn't already exist
    """

    orig_path = Path.cwd()
    was_created = False
    if not path.is_dir() and create_missing:
        path.mkdir(0o777)
        was_created = True

    try:
        os.chdir(path.as_posix())
        yield path
    finally:
        os.chdir(orig_path.as_posix())
        if was_created:
            shutil.rmtree(path)
