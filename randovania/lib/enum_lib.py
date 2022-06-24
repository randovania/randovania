from typing import TypeVar, Iterator

T = TypeVar("T")


def iterate_enum(enum_class: type[T]) -> Iterator[T]:
    yield from enum_class
