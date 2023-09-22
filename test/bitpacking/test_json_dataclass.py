from __future__ import annotations

import dataclasses
import datetime
import uuid
from enum import Enum
from typing import NamedTuple

import pytest

from randovania.bitpacking.construct_pack import construct_for_type
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
    d: tuple[int, ...]


@dataclasses.dataclass()
class D2OldSyntax(JsonDataclass):
    a: A | None
    b: D1


class N(NamedTuple):
    a: int
    b: bool


@dataclasses.dataclass()
class HasDict(JsonDataclass):
    a: int
    b: dict[uuid.UUID, int]
    c: list[RandovaniaGame]
    d: list
    e: dict
    f: datetime.datetime
    g: N
    h: tuple[int, RandovaniaGame, str]


@pytest.fixture(
    params=[
        {
            "instance": D2(a=A.bar, b=D1(a=5, b="foo", c=1), c=uuid.UUID("00000000-0000-1111-0000-000000000000"), d=()),
            "json": {
                "a": "bar",
                "b": {"a": 5, "b": "foo", "c": 1},
                "c": "00000000-0000-1111-0000-000000000000",
                "d": [],
            },
        },
        {
            "instance": D2(
                a=None, b=D1(a=5, b="foo", c=2), c=uuid.UUID("00000000-0000-1111-0000-000000000000"), d=(10, 25, 20)
            ),
            "json": {
                "a": None,
                "b": {"a": 5, "b": "foo", "c": 2},
                "c": "00000000-0000-1111-0000-000000000000",
                "d": [10, 25, 20],
            },
        },
        {
            "instance": D2(a=None, b=D1(a=5, b="foo"), c=uuid.UUID("00000000-0000-1111-0000-000000000000"), d=(50,)),
            "json": {
                "a": None,
                "b": {"a": 5, "b": "foo", "c": 5},
                "c": "00000000-0000-1111-0000-000000000000",
                "d": [50],
            },
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


def test_has_dict():
    value = HasDict(
        10,
        {uuid.UUID("77000000-0000-1111-0000-000000000000"): 15},
        [RandovaniaGame.BLANK],
        [None],
        {},
        datetime.datetime(2019, 1, 3, 2, 50, tzinfo=datetime.UTC),
        N(2403, True),
        (60, RandovaniaGame.METROID_PRIME_ECHOES, "foo"),
    )
    data = {
        "a": 10,
        "b": {"77000000-0000-1111-0000-000000000000": 15},
        "c": ["blank"],
        "d": [None],
        "e": {},
        "f": "2019-01-03T02:50:00+00:00",
        "g": {"a": 2403, "b": True},
        "h": [60, "prime2", "foo"],
    }

    assert HasDict.from_json(data) == value
    assert value.as_json == data


def test_generic_list_errors():
    with pytest.raises(TypeError):
        construct_for_type(list)
