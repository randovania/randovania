from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from typing import Annotated, Any

    from randovania.lib.json_lib import JsonObject_RO


type TypedBytes[T] = Annotated[bytes, T]

type TypedJsonObject[T] = Annotated[JsonObject_RO, T]

type SioDataType = str | bytes | Mapping[str, SioDataType] | Sequence[SioDataType]


def args_to_sio_data(*args: Any) -> SioDataType | tuple[SioDataType, ...]:
    if len(args) == 1:
        return typing.cast("SioDataType", args[0])
    else:
        return typing.cast("tuple[SioDataType, ...]", args)
