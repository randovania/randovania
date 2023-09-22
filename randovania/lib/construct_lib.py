from __future__ import annotations

import json
import typing
from typing import Any

import construct
from construct import CString, Flag, If, PrefixedArray, Rebuild, Struct, VarInt

String = CString("utf-8")


def convert_to_raw_python(value: Any) -> Any:
    if isinstance(value, list):
        return [convert_to_raw_python(item) for item in value]

    if isinstance(value, dict):
        return {key: convert_to_raw_python(item) for key, item in value.items() if not key.startswith("_")}

    if isinstance(value, construct.EnumIntegerString):
        return str(value)

    return value


def is_path_not_equals_to(path: construct.Path, value: typing.Any) -> construct.BinExpr:
    return path != value


def OptionalValue(subcon: construct.Construct) -> construct.Construct:
    return construct.FocusedSeq(
        "value",
        present=Rebuild(Flag, is_path_not_equals_to(construct.this.value, None)),
        value=If(construct.this.present, subcon),
    )


class DictAdapter(construct.Adapter):
    def _decode(self, obj: construct.ListContainer, context: construct.Container, path: str) -> construct.Container:
        result: construct.Container = construct.Container()
        last = {}
        for i, item in enumerate(obj):
            key = item.key
            if key in result:
                raise construct.ConstructError(f"Key {key} found twice in object", path)
            last[key] = i
            result[key] = item.value
        return result

    def _encode(self, obj: construct.Container, context: construct.Container, path: str) -> construct.ListContainer:
        return construct.ListContainer(construct.Container(key=type_, value=item) for type_, item in obj.items())


def ConstructDict(subcon: construct.Construct) -> construct.Construct:
    return DictAdapter(
        PrefixedArray(
            VarInt,
            Struct(
                key=String,
                value=subcon,
            ),
        )
    )


class JsonEncodedValueAdapter(construct.Adapter):
    def _decode(self, obj: str, context: construct.Container, path: str) -> typing.Any:
        return json.loads(obj)

    def _encode(self, obj: typing.Any, context: construct.Container, path: str) -> str:
        return json.dumps(obj, separators=(",", ":"))


JsonEncodedValue = JsonEncodedValueAdapter(String)
