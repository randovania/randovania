import json
from typing import Any

import construct
from construct import CString, Rebuild, Flag, If, PrefixedArray, VarInt, Struct

String = CString("utf-8")


def convert_to_raw_python(value) -> Any:
    if isinstance(value, construct.ListContainer):
        return [
            convert_to_raw_python(item)
            for item in value
        ]

    if isinstance(value, construct.Container):
        return {
            key: convert_to_raw_python(item)
            for key, item in value.items()
            if not key.startswith("_")
        }

    if isinstance(value, construct.EnumIntegerString):
        return str(value)

    return value


def OptionalValue(subcon):
    return construct.FocusedSeq(
        "value",
        present=Rebuild(Flag, construct.this.value != None),
        value=If(construct.this.present, subcon),
    )


class DictAdapter(construct.Adapter):
    def _decode(self, obj: construct.ListContainer, context, path):
        result = construct.Container()
        last = {}
        for i, item in enumerate(obj):
            key = item.key
            if key in result:
                raise construct.ConstructError(f"Key {key} found twice in object", path)
            last[key] = i
            result[key] = item.value
        return result

    def _encode(self, obj: construct.Container, context, path):
        return construct.ListContainer(
            construct.Container(key=type_, value=item)
            for type_, item in obj.items()
        )


def ConstructDict(subcon):
    return DictAdapter(PrefixedArray(VarInt, Struct(
        key=String,
        value=subcon,
    )))


JsonEncodedValue = construct.ExprAdapter(
    String,
    # Decode
    lambda obj, ctx: json.loads(obj),
    # Encode
    lambda obj, ctx: json.dumps(obj),
)
