from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import aiofiles

if TYPE_CHECKING:
    from collections.abc import Hashable
    from pathlib import Path


def _hook_for_raise_on_duplicate_keys(ordered_pairs: list[tuple[Hashable, Any]]) -> dict:
    """Raise ValueError if a duplicate key exists in provided ordered list of pairs, otherwise return a dict."""
    dict_out = {}
    for key, val in ordered_pairs:
        if key in dict_out:
            raise ValueError(f"Duplicate key: {key}")
        else:
            dict_out[key] = val
    return dict_out


def read_path(path: Path, *, raise_on_duplicate_keys: bool = False) -> dict | list:
    with path.open("r") as file:
        return json.load(file, object_pairs_hook=_hook_for_raise_on_duplicate_keys if raise_on_duplicate_keys else None)


def read_dict(path: Path) -> dict:
    result = read_path(path)
    assert isinstance(result, dict)
    return result


def write_path(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(encode(data))


def encode(data: Any) -> str:
    return json.dumps(data, indent=4, separators=(",", ": "))


async def read_path_async(path: Path, *, raise_on_duplicate_keys: bool = False) -> dict | list:
    async with aiofiles.open(path) as f:
        return json.loads(
            await f.read(), object_pairs_hook=_hook_for_raise_on_duplicate_keys if raise_on_duplicate_keys else None
        )


def dumps_small(obj: dict | list) -> str:
    return json.dumps(obj, separators=(",", ":"))
