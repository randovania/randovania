from __future__ import annotations

import pytest

from randovania.lib import json_lib


def test_read_raise_duplicate_keys(tmp_path):
    path = tmp_path.joinpath("sample.json")
    path.write_text('{"a": 1, "b": 2, "a": 3}')

    with pytest.raises(ValueError, match='Duplicate key: a'):
        json_lib.read_path(path, raise_on_duplicate_keys=True)


def test_read_ignore_duplicate_keys(tmp_path):
    path = tmp_path.joinpath("sample.json")
    path.write_text('{"a": 1, "b": 2, "a": 3}')

    assert list(json_lib.read_path(path).items()) == [
        ("a", 3),
        ("b", 2),
    ]


def test_dumps_small():
    assert json_lib.dumps_small({"a": 1, "b": 3}) == '{"a":1,"b":3}'
