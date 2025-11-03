from __future__ import annotations

import contextlib
from enum import Enum
from typing import Protocol


class DebugPrintFunction(Protocol):
    def __call__(self, __s: str) -> None: ...


class LogLevel(int, Enum):
    SILENT = 0
    NORMAL = 1
    HIGH = 2
    EXTREME = 3
    MORE_EXTREME = 4


_DEBUG_LEVEL = LogLevel.SILENT


def _print_function(s: str):
    print(s)


print_function: DebugPrintFunction = _print_function


def set_level(level: LogLevel):
    global _DEBUG_LEVEL
    if isinstance(level, int):
        # clamp to within the defined log levels
        level = max(LogLevel.SILENT, min(level, max(LogLevel)))
        _DEBUG_LEVEL = LogLevel(level)
    else:
        _DEBUG_LEVEL = LogLevel.SILENT


def debug_level() -> LogLevel:
    return _DEBUG_LEVEL


@contextlib.contextmanager
def with_level(level: LogLevel):
    current_level = debug_level()
    try:
        set_level(level)
        yield
    finally:
        set_level(current_level)


def debug_print(message: str):
    if _DEBUG_LEVEL > LogLevel.SILENT:
        print_function(message)
