from typing import TypeVar, Type, Iterator

T = TypeVar("T")


def iterate_enum(enum_class: Type[T]) -> Iterator[T]:
    yield from enum_class
