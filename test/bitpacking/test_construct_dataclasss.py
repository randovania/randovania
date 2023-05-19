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
