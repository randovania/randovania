from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    from collections.abc import Iterator

T = TypeVar("T", bound=Enum)


def iterate_enum(enum_class: type[T]) -> Iterator[T]:
    assert issubclass(enum_class, Enum)
    yield from enum_class


def add_long_name(enum_class: type[T], names: dict[T, str]) -> None:
    add_per_enum_field(enum_class, "long_name", names)


def add_per_enum_field(enum_class: type[T], field_name: str, names: dict[T, Any]) -> None:
    if set(enum_class) != set(names.keys()):
        raise ValueError(f"{field_name} for {enum_class} are not synchronized")

    for key, value in names.items():
        setattr(key, field_name, value)
