from __future__ import annotations

import dataclasses
import datetime
import functools
import json
import typing
import uuid
from enum import Enum

import construct
from frozendict import frozendict

from randovania.lib import construct_lib, type_lib

if typing.TYPE_CHECKING:
    from _typeshed import DataclassInstance

    from randovania.lib.construct_stub import CodeGen
    from randovania.lib.json_lib import JsonType

BinStr = construct.PascalString(construct.VarInt, "utf-8")


def _bin_str_emitbuild(code: CodeGen) -> str:
    fname = f"build_str_{code.allocateId()}"
    code.append(f"""
        def {fname}(obj: str, io, this):
            encoded = obj.encode("utf-8")
            obj = len(encoded)
            {construct_lib.compile_build_struct(construct.VarInt, code)}
            io.write(encoded)
            return obj
        """)
    return f"{fname}(obj, io, this)"


construct_lib.add_emit_build(BinStr, _bin_str_emitbuild)


T = typing.TypeVar("T")


@typing.runtime_checkable
class JsonEncodable(typing.Protocol):
    @classmethod
    def from_json(cls, value: JsonType) -> typing.Self: ...

    def as_json(self) -> JsonType: ...


class DictAdapter(construct.Adapter):
    def _decode(self, obj: list, context: construct.Container, path: str) -> dict:
        return dict(obj)

    def _encode(self, obj: dict, context: construct.Container, path: str) -> list:
        return list(obj.items())


class ConstructTypedStruct(construct.Adapter, typing.Generic[T]):
    def __init__(self, cls: type[T], field_types: dict[str, type]):
        self.cls = cls
        self.field_types = field_types

        fields = [
            construct.Renamed(
                construct_for_type(field_type),
                field_name,
            )
            for field_name, field_type in field_types.items()
        ]
        super().__init__(construct.Struct(*fields))

    def _decode(self, obj: construct.Container, context: construct.Container, path: str) -> T:
        return self.cls(**{field_name: obj[field_name] for field_name in self.field_types.keys()})

    def _encode(self, obj: T, context: construct.Container, path: str) -> construct.Container:
        return construct.Container((field_name, getattr(obj, field_name)) for field_name in self.field_types.keys())

    def _emitbuild(self, code: CodeGen) -> str:
        fname = f"build_typed_struct_{code.allocateId()}"
        block = f"""
            def {fname}(obj, io, this):
                obj = Container([
"""
        for field_name in self.field_types.keys():
            block += f"                    ({repr(field_name)}, obj.{field_name}),\n"
        block += f"""
                ])
                return {construct_lib.compile_build_struct(self.subcon, code)}
        """
        code.append(block)
        return f"{fname}(obj, io, this)"


def _construct_dataclass(cls: type[DataclassInstance]) -> ConstructTypedStruct:
    resolved_types = typing.get_type_hints(cls)
    field_types: dict[str, type] = {
        field.name: resolved_types[field.name] for field in dataclasses.fields(cls) if field.init
    }
    return ConstructTypedStruct(cls, field_types)


def _construct_for_named_tuple(cls: type[typing.NamedTuple]) -> construct.Construct:
    resolved_types = typing.get_type_hints(cls)

    field_types: dict[str, type] = {field_name: resolved_types[field_name] for field_name in cls._fields}

    return ConstructTypedStruct(cls, field_types)


class UUIDAdapter(construct.Adapter):
    def __init__(self) -> None:
        super().__init__(construct.Bytes(16))

    def _decode(self, obj: bytes, context: construct.Container, path: str) -> uuid.UUID:
        return uuid.UUID(bytes=obj)

    def _encode(self, obj: uuid.UUID, context: construct.Container, path: str) -> bytes:
        return obj.bytes

    def _emitparse(self, code: CodeGen) -> str:
        code.append("import uuid")
        return "uuid.UUID(bytes=io.read(16))"

    def _emitbuild(self, code: CodeGen) -> str:
        return "(io.write(obj.bytes), obj)[1]"


class DatetimeAdapter(construct.Adapter):
    def __init__(self) -> None:
        super().__init__(construct.ZigZag)

    def _decode(self, obj: int, context: construct.Container, path: str) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(obj / 10000000, tz=datetime.UTC)

    def _encode(self, obj: datetime.datetime, context: construct.Container, path: str) -> int:
        if obj.tzinfo != datetime.UTC:
            raise construct.ConstructError(f"{obj} is not an UTC datetime", path)

        return int(obj.timestamp() * 10000000)

    def _emitbuild(self, code: CodeGen) -> str:
        construct_lib.zigzag_emitbuild(code)
        return "_zigzag_build(int(obj.timestamp() * 10000000), io, this)"


_direct_mapping: dict[type, construct.Construct] = {
    bool: construct.Flag,
    int: construct.ZigZag,
    str: BinStr,
    bytes: construct.Prefixed(construct.VarInt, construct.GreedyBytes),
    uuid.UUID: UUIDAdapter(),
    datetime.datetime: DatetimeAdapter(),
}


def _tuple_unwrap(con: construct.Construct) -> construct.ExprAdapter:
    return construct.ExprAdapter(
        con,
        decoder=lambda obj, ctx: tuple(obj),
        encoder=lambda obj, ctx: obj,
    )


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

    if isinstance(type_, type) and issubclass(type_, Enum):
        enum_arr = list(type_)
        return construct.ExprAdapter(
            construct.VarInt,
            decoder=lambda obj, ctx: enum_arr[obj],
            encoder=lambda obj, ctx: enum_arr.index(obj),
        )

    elif type_lib.is_named_tuple(type_):
        return _construct_for_named_tuple(typing.cast("type[typing.NamedTuple]", type_))

    elif type_origin is list:
        if type_args := typing.get_args(type_):
            value_type = type_args[0]
        else:
            value_type = typing.Any

        return construct.PrefixedArray(construct.VarInt, construct_for_type(value_type))

    elif type_origin is tuple:
        type_args = typing.get_args(type_)
        if type_args:
            if len(type_args) == 2 and type_args[1] == Ellipsis:
                return _tuple_unwrap(construct.PrefixedArray(construct.VarInt, construct_for_type(type_args[0])))
            else:
                return _tuple_unwrap(construct.Sequence(*[construct_for_type(value_type) for value_type in type_args]))
        else:
            return _tuple_unwrap(construct.PrefixedArray(construct.VarInt, construct_for_type(typing.Any)))

    elif type_origin in (dict, frozendict):
        if type_args := typing.get_args(type_):
            key_type, value_type = type_args
        else:
            key_type, value_type = str, typing.Any

        return DictAdapter(
            construct.PrefixedArray(
                construct.VarInt,
                construct.Sequence(
                    construct_for_type(key_type),
                    construct_for_type(value_type),
                ),
            )
        )

    elif dataclasses.is_dataclass(type_):
        return _construct_dataclass(type_)

    elif issubclass(type_, JsonEncodable):
        json_type: type[JsonEncodable] = type_
        return construct.ExprAdapter(
            BinStr,
            encoder=lambda obj, ctx: json.dumps(obj.as_json, separators=(",", ":")),
            decoder=lambda obj, ctx: json_type.from_json(json.loads(obj)),
        )

    raise TypeError(f"Unsupported type: {type_}.")


@functools.cache
def compiled_construct_for_type(type_: type) -> construct.Construct:
    return construct_for_type(type_).compile(
        # Uncomment to inspect the generated code
        # f"compiled_{type_.__name__}.py"
    )


def encode(obj: T, type_: type[T] | None = None) -> bytes:
    if type_ is None:
        type_ = type(obj)
    t: type = type_  # workaround for mypy considering type[T] not hashable
    return compiled_construct_for_type(t).build(obj)


def decode(data: bytes, type_: type[T]) -> T:
    t: type = type_
    return construct_for_type(t).parse(data)
