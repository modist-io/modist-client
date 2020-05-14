# -*- encoding: utf-8 -*-
# Copyright (c) 2020 Modist Team <admin@modist.io>
# ISC License <https://opensource.org/licenses/isc>

"""Contains strategies that are useful throughout all the log specific tests."""

import string
from logging import LogRecord, _nameToLevel
from types import TracebackType
from typing import Optional, Tuple, Type

from hypothesis.strategies import (
    SearchStrategy,
    composite,
    integers,
    sampled_from,
    text,
    tuples,
)

from ..strategies import builtin_exceptions, pathlib_path

Excinfo_T = Tuple[Type[Exception], Exception, Optional[TracebackType]]


@composite
def excinfo(
    draw,
    exception_type_strategy: Optional[SearchStrategy[Type[Exception]]] = None,
    message_strategy: Optional[SearchStrategy[str]] = None,
) -> Excinfo_T:
    """Composite strategy for constructing excinfo tuples."""

    exception_type = draw(
        builtin_exceptions(
            exclude=[UnicodeDecodeError, UnicodeEncodeError, UnicodeTranslateError]
        )
        if not exception_type_strategy
        else exception_type_strategy
    )
    exception = exception_type(
        draw(
            text(alphabet=string.printable, min_size=1)
            if not message_strategy
            else message_strategy
        )
    )

    return (
        exception_type,
        exception,
        exception.__traceback__,
    )


@composite
def log_record(
    draw,
    record_name_strategy: Optional[SearchStrategy[str]] = None,
    level_strategy: Optional[SearchStrategy[int]] = None,
    pathname_strategy: Optional[SearchStrategy[str]] = None,
    lineno_strategy: Optional[SearchStrategy[int]] = None,
    message_strategy: Optional[SearchStrategy[str]] = None,
    args_strategy: Optional[SearchStrategy[Tuple[str]]] = None,
    excinfo_strategy: Optional[SearchStrategy[Excinfo_T]] = None,
) -> LogRecord:
    """Composite strategy for constructing ``logging.LogRecord`` instances."""

    return LogRecord(
        name=draw(
            text(alphabet=string.printable, min_size=1)
            if not record_name_strategy
            else record_name_strategy
        ),
        level=draw(
            sampled_from(list(_nameToLevel.values()))
            if not level_strategy
            else level_strategy
        ),
        pathname=(
            draw(pathlib_path()).as_posix()
            if not pathname_strategy
            else draw(pathname_strategy)
        ),
        lineno=draw(integers(min_value=1) if not lineno_strategy else lineno_strategy),
        msg=draw(
            text(alphabet=string.printable, min_size=1)
            if not message_strategy
            else message_strategy
        ),
        args=draw(tuples() if not args_strategy else args_strategy),
        exc_info=draw(excinfo() if not excinfo_strategy else excinfo_strategy),
    )
