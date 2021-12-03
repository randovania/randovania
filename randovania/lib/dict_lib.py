import typing

X = typing.TypeVar("X")
Y = typing.TypeVar("Y")


def iterate_key_sorted(obj: dict[X, Y]) -> typing.Iterator[tuple[X, Y]]:
    return sorted(obj.items(), key=lambda it: it[0])
