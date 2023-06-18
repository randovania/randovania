from __future__ import annotations

import dataclasses
import datetime
import uuid
from enum import Enum
from typing import NamedTuple

from randovania.bitpacking import construct_dataclass
from randovania.bitpacking.json_dataclass import JsonDataclass


class A(Enum):
    Foo = "foo"
    Bar = "bar"


def test_encode_enum():
    data = A.Bar.value

    con = construct_dataclass.construct_for_type(A)
    encoded = con.build(data)
    decoded = con.parse(encoded)
    assert decoded == data


def test_encode_dict():
    data = {
        "foo": 16,
        "bar": 8,
    }

    con = construct_dataclass.construct_for_type(dict[str, int])
    encoded = con.build(data)
    decoded = con.parse(encoded)
    assert decoded == data


@dataclasses.dataclass()
class D:
    a: int
    b: str | None
    c: list[uuid.UUID]
    d: tuple[str, int]


def test_encode_dataclass():
    data = {
        "a": 2,
        "b": None,
        "c": ["00000000-0000-1111-0000-000000000000", "00000000-0000-1111-0000-000000000001"],
        "d": ["foo", 50]
    }

    con = construct_dataclass.construct_for_type(D)
    encoded = con.build(data)
    decoded = con.parse(encoded)
    assert decoded == data


@dataclasses.dataclass()
class K(JsonDataclass):
    a: str | None
    b: int


class L(NamedTuple):
    a: int
    b: bool


@dataclasses.dataclass()
class J(JsonDataclass):
    a: int
    b: str | None
    c: list[uuid.UUID]
    d: datetime.datetime
    e: K
    f: L


def test_encode_jsondataclass():
    reference = J(
        a=10,
        b=None,
        c=[uuid.UUID("00000000-0000-1111-0000-000000000001")],
        d=datetime.datetime(2020, 1, 30, 14, 20, tzinfo=datetime.timezone.utc),
        e=K(
            a="foo",
            b=-1,
        ),
        f=L(
            a=2403,
            b=True,
        ),
    )

    encoded = construct_dataclass.encode_json_dataclass(reference)
    assert encoded == (b"\x14\x00\x0100000000-0000-1111-0000-000000000001\x192020-01-30T14:20:00+00:0"
                       b"0\x01\x03foo\x01\xc6%\x01")

    decoded = construct_dataclass.decode_json_dataclass(encoded, J)
    assert decoded == reference


class NonJsonThing:
    a: int
    b: str

    def __init__(self, a, b):
        self.a = a
        self.b = b

    def __eq__(self, other):
        return isinstance(other, NonJsonThing) and other.a == self.a and other.b == self.b

    @property
    def as_json(self) -> dict:
        return {
            "a": self.a,
            "b": self.b,
        }

    @classmethod
    def from_json(cls, data: dict):
        return cls(data["a"], data["b"])


def test_encode_non_jsondataclass():
    x = NonJsonThing(5, "foo")

    encoded = construct_dataclass.encode_json_dataclass(x)
    decoded = construct_dataclass.decode_json_dataclass(encoded, NonJsonThing)

    assert encoded == b'\x14{"a": 5, "b": "foo"}'
    assert decoded == x

    pass