import dataclasses
from enum import Enum
from typing import Optional

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
    a: Optional[A]
    b: D1


@pytest.fixture(
    params=[
        {"instance": D2(a=A.bar, b=D1(a=5, b='foo', c=1)),
         "json": {'a': 'bar', 'b': {'a': 5, 'b': 'foo', 'c': 1}},
         },
        {"instance": D2(a=None, b=D1(a=5, b='foo', c=2)),
         "json": {'a': None, 'b': {'a': 5, 'b': 'foo', 'c': 2}},
         },
        {"instance": D2(a=None, b=D1(a=5, b='foo')),
         "json": {'a': None, 'b': {'a': 5, 'b': 'foo', 'c': 5}},
         }
    ],
    name="sample_values")
def _sample_values(request):
    yield request.param["instance"], request.param["json"]


def test_as_json(sample_values):
    value, data = sample_values
    assert value.as_json == data


def test_from_json(sample_values):
    value, data = sample_values
    assert D2.from_json(data) == value


def test_from_json_missing_field_with_default():
    value = D1(2, "foo")
    data = {"a": 2, "b": "foo"}
    assert D1.from_json(data) == value
