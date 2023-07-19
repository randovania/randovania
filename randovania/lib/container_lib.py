import typing

X = typing.TypeVar("X")
Y = typing.TypeVar("Y")


def iterate_key_sorted(obj: dict[X, Y]) -> list[tuple[X, Y]]:
    return sorted(obj.items(), key=lambda it: it[0])


def ensure_in_set(element: X, the_set: set[X], present: bool):
    if present:
        the_set.add(element)
    elif element in the_set:
        the_set.remove(element)


def zip2(a: typing.Iterable[X], b: typing.Iterable[Y], *, strict: bool = True) -> typing.Iterable[tuple[X, Y]]:
    """zip, but for 2 elements and always strict.
    Mainly because PyCharm doesn't do types correctly for zip :("""
    return zip(a, b, strict=strict)
