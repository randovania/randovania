import dataclasses
import uuid
from enum import Enum
from typing import Optional

import pytest

from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.games.game import RandovaniaGame


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
    c: uuid.UUID


@dataclasses.dataclass()
class D2OldSyntax(JsonDataclass):
    a: Optional[A]
    b: D1


@dataclasses.dataclass()
class HasDict(JsonDataclass):
    a: int
    b: dict[uuid.UUID, int]
    c: list[RandovaniaGame]


@pytest.fixture(
    params=[
        {"instance": D2(a=A.bar, b=D1(a=5, b='foo', c=1), c=uuid.UUID("00000000-0000-1111-0000-000000000000")),
         "json": {'a': 'bar', 'b': {'a': 5, 'b': 'foo', 'c': 1}, 'c': "00000000-0000-1111-0000-000000000000"},
         },
        {"instance": D2(a=None, b=D1(a=5, b='foo', c=2), c=uuid.UUID("00000000-0000-1111-0000-000000000000")),
         "json": {'a': None, 'b': {'a': 5, 'b': 'foo', 'c': 2}, 'c': "00000000-0000-1111-0000-000000000000"},
         },
        {"instance": D2(a=None, b=D1(a=5, b='foo'), c=uuid.UUID("00000000-0000-1111-0000-000000000000")),
         "json": {'a': None, 'b': {'a': 5, 'b': 'foo', 'c': 5}, 'c': "00000000-0000-1111-0000-000000000000"},
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


def test_from_json_old():
    value = D2OldSyntax(a=A.bar, b=D1(a=5, b='foo', c=1))
    data = {'a': 'bar', 'b': {'a': 5, 'b': 'foo', 'c': 1}}
    assert D2OldSyntax.from_json(data) == value


def test_from_json_missing_field_with_default():
    value = D1(2, "foo")
    data = {"a": 2, "b": "foo"}
    assert D1.from_json(data) == value


def test_has_dict():
    value = HasDict(10, {uuid.UUID("77000000-0000-1111-0000-000000000000"): 15},
                    [RandovaniaGame.BLANK])
    data = {"a": 10, "b": {"77000000-0000-1111-0000-000000000000": 15}, "c": ["blank"]}

    assert HasDict.from_json(data) == value
    assert value.as_json == data
