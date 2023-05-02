import types
import typing


def resolve_optional(type_: type) -> tuple[type, bool]:
    origin = typing.get_origin(type_)

    if origin is typing.Union or isinstance(type_, types.UnionType):
        args = typing.get_args(type_)
        if (len(args) == 2 and args[1] is types.NoneType  # noqa: E721
        ):
            return args[0], True

    return type_, False
