import dataclasses
import uuid
from enum import Enum

from randovania.bitpacking.construct_dataclass import construct_for_type


class A(Enum):
    foo = "foo"
    bar = "bar"


def test_encode_enum():
    data = A.bar.value

    con = construct_for_type(A)
    encoded = con.build(data)
    decoded = con.parse(encoded)
    assert decoded == data


def test_encode_dict():
    data = {
        "foo": 16,
        "bar": 8,
    }

    con = construct_for_type(dict[str, int])
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

    con = construct_for_type(D)
    encoded = con.build(data)
    decoded = con.parse(encoded)
    assert decoded == data
