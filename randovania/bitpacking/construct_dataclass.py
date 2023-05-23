import dataclasses
import typing
import uuid
from enum import Enum

import construct

from randovania.lib import type_lib

BinStr = construct.PascalString(construct.VarInt, "utf-8")


class DictAdapter(construct.Adapter):
    def _decode(self, obj: list, context, path):
        return dict(obj)

    def _encode(self, obj: dict, context, path):
        return list(obj.items())


def construct_for_dataclass(cls) -> construct.Construct:
    fields = []

    for field in dataclasses.fields(cls):
        if not field.init:
            continue
        fields.append(construct.Renamed(
            construct_for_type(field.type),
            field.name,
        ))

    return construct.Struct(*fields)


_direct_mapping = {
    bool: construct.Flag,
    int: construct.VarInt,
    str: BinStr,
    uuid.UUID: BinStr,
}


def construct_for_type(type_: type) -> construct.Construct:
    type_, is_optional = type_lib.resolve_optional(type_)

    if is_optional:
        return construct.ExprAdapter(
            construct.PrefixedArray(construct.Byte, construct_for_type(type_)),
            decoder=lambda obj, ctx: obj[0] if obj else None,
            encoder=lambda obj, ctx: [obj] if obj is not None else [],
        )

    if type_ in _direct_mapping:
        return _direct_mapping[type_]

    if issubclass(type_, Enum):
        return construct.Enum(construct.VarInt, **{
            value.name: i
            for i, value in enumerate(type_)
        })

    elif typing.get_origin(type_) == list:
        if type_args := typing.get_args(type_):
            value_type = type_args[0]
        else:
            value_type = typing.Any

        return construct.PrefixedArray(construct.VarInt, construct_for_type(value_type))

    elif typing.get_origin(type_) == dict:
        if type_args := typing.get_args(type_):
            key_type, value_type = type_args
        else:
            key_type, value_type = str, typing.Any

        return DictAdapter(construct.PrefixedArray(
            construct.VarInt,
            construct.Sequence(
                construct_for_type(key_type),
                construct_for_type(value_type),
            ),
        ))

    elif dataclasses.is_dataclass(type_):
        return construct_for_dataclass(type_)

    raise TypeError(f"Unsupported type: {type_}.")
