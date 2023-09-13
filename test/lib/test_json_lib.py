from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from randovania.lib import json_lib

if TYPE_CHECKING:
    from pathlib import Path


def test_read_raise_duplicate_keys(tmp_path: Path) -> None:
    path = tmp_path.joinpath("sample.json")
    path.write_text('{"a": 1, "b": 2, "a": 3}')

    with pytest.raises(ValueError, match="Duplicate key: a"):
        json_lib.read_path(path, raise_on_duplicate_keys=True)


def test_read_ignore_duplicate_keys(tmp_path: Path) -> None:
    path = tmp_path.joinpath("sample.json")
    path.write_text('{"a": 1, "b": 2, "a": 3}')

    d = json_lib.read_path(path)
    assert isinstance(d, dict)
    assert list(d.items()) == [
        ("a", 3),
        ("b", 2),
    ]


def test_dumps_small() -> None:
    assert json_lib.dumps_small({"a": 1, "b": 3}) == '{"a":1,"b":3}'
