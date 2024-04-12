from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import aiofiles
import orjson

USE_ORJSON = False

if TYPE_CHECKING:
    from pathlib import Path


def read_path(path: Path) -> dict | list:
    if USE_ORJSON:
        return orjson.loads(path.read_bytes())
    else:
        with path.open("r") as file:
            return json.load(file)


def read_dict(path: Path) -> dict:
    result = read_path(path)
    assert isinstance(result, dict)
    return result


def write_path(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=4, separators=(",", ": ")))


async def read_path_async(path: Path) -> dict | list:
    if USE_ORJSON:
        async with aiofiles.open(path, "rb") as f:
            return orjson.loads(await f.read())
    else:
        async with aiofiles.open(path) as f:
            return json.loads(await f.read())


def dumps_small(obj: dict | list) -> str:
    return json.dumps(obj, separators=(",", ":"))
