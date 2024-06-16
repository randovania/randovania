from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

_DEBUG_LEVEL = 0


def print_function(s: str) -> None:
    print(s)


def set_level(level: int) -> None:
    global _DEBUG_LEVEL
    if isinstance(level, int):
        _DEBUG_LEVEL = level
    else:
        _DEBUG_LEVEL = 0


def debug_level() -> int:
    return _DEBUG_LEVEL


@contextlib.contextmanager
def with_level(level: int) -> Iterator:
    current_level = debug_level()
    try:
        set_level(level)
        yield
    finally:
        set_level(current_level)


def debug_print(message: str) -> None:
    if _DEBUG_LEVEL > 0:
        print_function(message)
