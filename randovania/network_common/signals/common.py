from __future__ import annotations

import typing

from randovania.lib.json_lib import JsonPrimitive

if typing.TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from typing import Any

    from randovania.lib.json_lib import JsonObject_RO


type TypedBytes[T] = bytes

type TypedJsonObject[T] = JsonObject_RO

# the socketio stubs are incorrect about what's actually supported. annoying
type SioDataType = JsonPrimitive | bytes | Mapping[str, SioDataType] | Sequence[SioDataType]


def args_to_sio_data(*args: Any) -> SioDataType | tuple[SioDataType, ...]:
    if len(args) == 1:
        return typing.cast("SioDataType", args[0])
    else:
        return typing.cast("tuple[SioDataType, ...]", args)
