from __future__ import annotations

import dataclasses
import datetime
import uuid
from enum import Enum
from typing import NamedTuple

from randovania.bitpacking import construct_pack
from randovania.bitpacking.json_dataclass import JsonDataclass


class A(Enum):
    Foo = "foo"
    Bar = "bar"


def test_encode_enum():
    data = A.Bar

    encoded = construct_pack.encode(data)
    decoded = construct_pack.decode(encoded, A)

    assert decoded == data


def test_encode_uuid():
    data = uuid.UUID("948c1795-3305-4f9f-aca8-81aff73924ae")

    encoded = construct_pack.encode(data)
    decoded = construct_pack.decode(encoded, uuid.UUID)

    assert decoded == data
    assert encoded == b"\x94\x8c\x17\x953\x05O\x9f\xac\xa8\x81\xaf\xf79$\xae"


def test_encode_datetime():
    data = datetime.datetime(2020, 1, 30, 14, 20, 50, 253, tzinfo=datetime.UTC)

    encoded = construct_pack.encode(data)
    decoded = construct_pack.decode(encoded, datetime.datetime)

    assert decoded == data
    assert encoded == b"\xc4\xdb\xee\xb8\xb4\xe6\x928"


def test_encode_dict():
    data = {
        "foo": 16,
        "bar": 8,
    }

    encoded = construct_pack.encode(data, dict[str, int])
    decoded = construct_pack.decode(encoded, dict[str, int])
    assert decoded == data


@dataclasses.dataclass()
class D:
    a: int
    b: str | None
    c: list[uuid.UUID]
    d: tuple[str, int]


def test_encode_dataclass():
    data = D(
        a=2,
        b=None,
        c=[uuid.UUID("00000000-0000-1111-0000-000000000000"), uuid.UUID("00000000-0000-1111-0000-000000000001")],
        d=("foo", 50),
    )

    encoded = construct_pack.encode(data)
    decoded = construct_pack.decode(encoded, D)
    assert decoded == data


@dataclasses.dataclass()
class K(JsonDataclass):
    a: str | None
    b: int


class L(NamedTuple):
    a: int
    b: bool


def test_encode_namedtuple():
    data = L(10, False)

    encoded = construct_pack.encode(data)
    decoded = construct_pack.decode(encoded, L)

    assert decoded == data
    assert encoded == b"\x14\x00"


@dataclasses.dataclass()
class J(JsonDataclass):
    a: int
    b: str | None
    c: list[uuid.UUID]
    d: datetime.datetime
    e: K
    f: L


def test_encode_complex_dataclass():
    reference = J(
        a=10,
        b=None,
        c=[uuid.UUID("00000000-0000-1111-0000-000000000001")],
        d=datetime.datetime(2020, 1, 30, 14, 20, tzinfo=datetime.UTC),
        e=K(
            a="foo",
            b=-1,
        ),
        f=L(
            a=2403,
            b=True,
        ),
    )

    encoded = construct_pack.encode(reference)
    assert encoded == (
        b"\x14\x00\x01\x00\x00\x00\x00\x00\x00\x11\x11\x00\x00\x00\x00\x00"
        b"\x00\x00\x01\x80\xa0\x83\xdc\xb0\xe6\x928\x01\x03foo\x01\xc6%\x01"
    )

    decoded = construct_pack.decode(encoded, J)
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

    encoded = construct_pack.encode(x)
    decoded = construct_pack.decode(encoded, NonJsonThing)

    assert encoded == b'\x11{"a":5,"b":"foo"}'
    assert decoded == x
