import dataclasses
import datetime
import functools
import typing
import uuid
from enum import Enum

import construct
from frozendict import frozendict

from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.lib import type_lib
from randovania.lib.construct_lib import convert_to_raw_python

BinStr = construct.PascalString(construct.VarInt, "utf-8")


class DictAdapter(construct.Adapter):
    def _decode(self, obj: list, context, path):
        return dict(obj)

    def _encode(self, obj: dict, context, path):
        return list(obj.items())


def _construct_for_dataclass(cls) -> construct.Construct:
    resolved_types = typing.get_type_hints(cls)

    fields = []

    for field in dataclasses.fields(cls):
        if not field.init:
            continue

        field_type = field.type
        if isinstance(field_type, str):
            field_type = resolved_types[field.name]

        fields.append(construct.Renamed(
            construct_for_type(field_type),
            field.name,
        ))

    return construct.Struct(*fields)


def _construct_for_named_tuple(cls) -> construct.Construct:
    resolved_types = typing.get_type_hints(cls)

    fields = [
        construct.Renamed(
            construct_for_type(resolved_types[field_name]),
            field_name
        ) for field_name in cls._fields
    ]

    return construct.Struct(*fields)


_direct_mapping = {
    bool: construct.Flag,
    int: construct.ZigZag,
    str: BinStr,
    uuid.UUID: construct.PaddedString(36, "ascii"),
    datetime.datetime: BinStr,
}


@functools.cache
def construct_for_type(type_: type) -> construct.Construct:
    type_, is_optional = type_lib.resolve_optional(type_)

    if is_optional:
        return construct.ExprAdapter(
            construct.PrefixedArray(construct.Byte, construct_for_type(type_)),
            decoder=lambda obj, ctx: obj[0] if obj else None,
            encoder=lambda obj, ctx: [obj] if obj is not None else [],
        )

    type_origin = typing.get_origin(type_)

    if type_ in _direct_mapping:
        return _direct_mapping[type_]

    if issubclass(type_, Enum):
        return construct.Enum(construct.VarInt, **{
            value.value: i
            for i, value in enumerate(type_)
        })

    elif type_lib.is_named_tuple(type_):
        return _construct_for_named_tuple(type_)

    elif type_origin == list:
        if type_args := typing.get_args(type_):
            value_type = type_args[0]
        else:
            value_type = typing.Any

        return construct.PrefixedArray(construct.VarInt, construct_for_type(value_type))

    elif type_origin == tuple:
        type_args = typing.get_args(type_)
        if type_args:
            if len(type_args) == 2 and type_args[1] == Ellipsis:
                return construct.PrefixedArray(construct.VarInt, construct_for_type(type_args[0]))
            else:
                return construct.Sequence(*[
                    construct_for_type(value_type)
                    for value_type in type_args
                ])
        else:
            return construct.PrefixedArray(construct.VarInt, construct_for_type(typing.Any))

    elif type_origin in (dict, frozendict):
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
        return _construct_for_dataclass(type_)

    raise TypeError(f"Unsupported type: {type_}.")


T = typing.TypeVar("T", bound=JsonDataclass)


def encode_json_dataclass(obj: JsonDataclass) -> bytes:
    return construct_for_type(type(obj)).build(obj.as_json)


def decode_json_dataclass(data: bytes, type_: type[T]) -> T:
    decoded = construct_for_type(type_).parse(data)
    return type_.from_json(convert_to_raw_python(decoded))
