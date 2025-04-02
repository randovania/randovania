from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, cast

import aiofiles

if TYPE_CHECKING:
    from collections.abc import Hashable
    from pathlib import Path
    from typing import Any, TypeAlias

_JsonPrimitive: TypeAlias = str | int | float | bool | None

_JsonType_RO: TypeAlias = Mapping[str, "_JsonType_RO"] | Sequence["_JsonType_RO"] | _JsonPrimitive
"""Covariant type alias useful when accepting read-only input."""

JsonObject: TypeAlias = dict[str, "JsonType"]
JsonType: TypeAlias = JsonObject | list["JsonType"] | _JsonPrimitive
"""Invariant and mutable type alias. Use `typing.cast()` or a type guard if more specificity is needed."""


def _hook_for_raise_on_duplicate_keys(ordered_pairs: list[tuple[Hashable, Any]]) -> dict:
    """Raise ValueError if a duplicate key exists in provided ordered list of pairs, otherwise return a dict."""
    dict_out = {}
    for key, val in ordered_pairs:
        if key in dict_out:
            raise ValueError(f"Duplicate key: {key}")
        else:
            dict_out[key] = val
    return dict_out


def read_path(path: Path, *, raise_on_duplicate_keys: bool = False) -> JsonType:
    with path.open("r") as file:
        return json.load(file, object_pairs_hook=_hook_for_raise_on_duplicate_keys if raise_on_duplicate_keys else None)


def read_dict(path: Path) -> JsonObject:
    result = read_path(path)
    return cast("JsonObject", result)


def write_path(path: Path, data: _JsonType_RO) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(encode(data))


def encode(data: _JsonType_RO) -> str:
    return json.dumps(data, indent=4, separators=(",", ": "))


async def read_path_async(path: Path, *, raise_on_duplicate_keys: bool = False) -> JsonType:
    async with aiofiles.open(path) as f:
        return json.loads(
            await f.read(), object_pairs_hook=_hook_for_raise_on_duplicate_keys if raise_on_duplicate_keys else None
        )


def dumps_small(obj: _JsonType_RO) -> str:
    return json.dumps(obj, separators=(",", ":"))
