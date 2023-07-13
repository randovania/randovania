from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from collections.abc import Iterator

T = TypeVar("T")


def iterate_enum(enum_class: type[T]) -> Iterator[T]:
    yield from enum_class


def add_long_name(enum_class: type[T], names: dict[T, str]) -> None:
    add_per_enum_field(enum_class, "long_name", names)


def add_per_enum_field(enum_class: type[T], field_name: str, names: dict[T, str]) -> None:
    if set(enum_class) != set(names.keys()):
        raise ValueError(f"{field_name} for {enum_class} are not synchronized")

    for key, value in names.items():
        setattr(key, field_name, value)
