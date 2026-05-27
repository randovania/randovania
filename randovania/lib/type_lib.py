from __future__ import annotations

import inspect
import types
import typing


def resolve_optional(type_: type) -> tuple[type, bool]:
    origin = typing.get_origin(type_)

    if origin is typing.Union or isinstance(type_, types.UnionType):
        args = typing.get_args(type_)
        if len(args) == 2 and args[1] is types.NoneType:  # noqa: E721
            return args[0], True

    return type_, False


def is_named_tuple(type_: type) -> bool:
    return (
        inspect.isclass(type_)
        and issubclass(type_, tuple)
        and hasattr(type_, "__annotations__")
        and hasattr(type_, "_fields")
        and hasattr(type_, "_field_defaults")
    )
