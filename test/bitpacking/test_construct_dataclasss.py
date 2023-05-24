from __future__ import annotations

import dataclasses
import datetime
import uuid
from enum import Enum

from randovania.bitpacking import construct_dataclass
from randovania.bitpacking.json_dataclass import JsonDataclass


class A(Enum):
    foo = "foo"
    bar = "bar"


def test_encode_enum():
    data = A.bar.value

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


def test_encode_dataclass():
    data = {
        "a": 2,
        "b": None,
        "c": ["00000000-0000-1111-0000-000000000000", "00000000-0000-1111-0000-000000000001"]
    }

    con = construct_dataclass.construct_for_type(D)
    encoded = con.build(data)
    decoded = con.parse(encoded)
    assert decoded == data


@dataclasses.dataclass()
class K(JsonDataclass):
    a: str | None
    b: int


@dataclasses.dataclass()
class J(JsonDataclass):
    a: int
    b: str | None
    c: list[uuid.UUID]
    d: datetime.datetime
    e: K


def test_encode_jsondataclass():
    reference = J(
        a=10,
        b=None,
        c=[uuid.UUID("00000000-0000-1111-0000-000000000001")],
        d=datetime.datetime(2020, 1, 30, 14, 20, tzinfo=datetime.timezone.utc),
        e=K(
            a="foo",
            b=-1,
        )
    )

    encoded = construct_dataclass.encode_json_dataclass(reference)
    assert encoded == (b"\x14\x00\x01$00000000-0000-1111-0000-000000000001\x192020-01-30T14:20:00+00:00"
                       b"\x01\x03foo\x01")

    decoded = construct_dataclass.decode_json_dataclass(encoded, J)
    assert decoded == reference
