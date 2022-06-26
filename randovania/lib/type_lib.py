import types
import typing


def resolve_optional(type_: type) -> tuple[type, bool]:
    origin = getattr(type_, "__origin__", None)
    if (origin is typing.Union or isinstance(type_, types.UnionType)) and (
            len(type_.__args__) == 2 and type_.__args__[1] is types.NoneType
    ):
        return type_.__args__[0], True
    return type_, False
