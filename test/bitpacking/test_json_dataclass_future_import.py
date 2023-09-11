"""
This file is duplicated from test_json_dataclass.py, but has the `from __future__ import annotations` line.
This causes all type hints in the file to be stored as strings in __annotations__ which need special handling.
"""

from __future__ import annotations

import dataclasses
from enum import Enum

import pytest

from randovania.bitpacking.json_dataclass import JsonDataclass


class A(Enum):
    foo = "foo"
    bar = "bar"


@dataclasses.dataclass()
class D1(JsonDataclass):
    a: int
    b: str
    c: int = 5


@dataclasses.dataclass()
class D2(JsonDataclass):
    a: A | None
    b: D1


@dataclasses.dataclass()
class D2OldSyntax(JsonDataclass):
    a: A | None
    b: D1


@pytest.fixture(
    params=[
        {
            "instance": D2(a=A.bar, b=D1(a=5, b="foo", c=1)),
            "json": {"a": "bar", "b": {"a": 5, "b": "foo", "c": 1}},
        },
        {
            "instance": D2(a=None, b=D1(a=5, b="foo", c=2)),
            "json": {"a": None, "b": {"a": 5, "b": "foo", "c": 2}},
        },
        {
            "instance": D2(a=None, b=D1(a=5, b="foo")),
            "json": {"a": None, "b": {"a": 5, "b": "foo", "c": 5}},
        },
    ],
)
def sample_values(request):
    return request.param["instance"], request.param["json"]


def test_as_json(sample_values):
    value, data = sample_values
    assert value.as_json == data


def test_from_json(sample_values):
    value, data = sample_values
    assert D2.from_json(data) == value


def test_from_json_old():
    value = D2OldSyntax(a=A.bar, b=D1(a=5, b="foo", c=1))
    data = {"a": "bar", "b": {"a": 5, "b": "foo", "c": 1}}
    assert D2OldSyntax.from_json(data) == value


def test_from_json_missing_field_with_default():
    value = D1(2, "foo")
    data = {"a": 2, "b": "foo"}
    assert D1.from_json(data) == value
