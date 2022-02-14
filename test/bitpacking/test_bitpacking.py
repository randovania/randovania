import dataclasses
from typing import Tuple, Iterator
from unittest.mock import MagicMock, call

import pytest

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder


@pytest.mark.parametrize("value", [
    10,
    65,
    0,
    1,
    2,
    134,
])
@pytest.mark.parametrize("limits", [
    (5, 20, 500),
    (3, 50, 150),
])
def test_encode_int_with_limits_round_trip(value: int,
                                           limits: Tuple[int, ...],
                                           ):
    # Run
    data = bitpacking._pack_encode_results(list(bitpacking.encode_int_with_limits(value, limits)))
    decoded = bitpacking.decode_int_with_limits(bitpacking.BitPackDecoder(data), limits)

    # Assert
    assert decoded == value


@pytest.fixture(
    params=[
        (0, (1, 4), [(0, 2)]),
        (1, (1, 4), [(1, 2), (0, 4)]),
        (5, (10,), [(5, 11)]),
        (50, (10,), [(50, 11)]),
        (5, (10, 100), [(5, 11)]),
        (50, (10, 100), [(10, 11), (40, 91)]),
        (5, (10, 100, 500), [(5, 11)]),
        (50, (10, 100, 500), [(10, 11), (40, 91)]),
        (500, (10, 100, 500), [(10, 11), (90, 91), (400, 401)]),
    ],
    name="limits_fixture")
def _limits_fixture(request):
    return request.param[0], request.param[1], request.param[2]


def test_encode_int_with_limits(limits_fixture):
    # Setup
    value, limits, encoded = limits_fixture

    # Run
    result = list(bitpacking.encode_int_with_limits(value, limits))

    # Assert
    assert result == encoded


def test_decode_int_with_limits(limits_fixture):
    # Setup
    value, limits, encoded = limits_fixture
    decoder = MagicMock()
    decoder.decode_single.side_effect = [part for part, _ in encoded]

    # Run
    result = bitpacking.decode_int_with_limits(decoder, limits)

    # Assert
    decoder.decode_single.assert_has_calls([
        call(limit)
        for _, limit in encoded
    ])
    assert result == value


@pytest.mark.parametrize(["value", "limits", "expected"], [
    (0, (1, 4), "u1"),
    (1, (1, 4), "u1u2"),
    (2, (1, 4), "u1u2"),
    (3, (1, 4), "u1u2"),
    (4, (1, 4), "u1u2"),
])
def test_encode_int_with_limits_bitstring(value, limits, expected):
    # Run
    result = bitpacking._format_string_for(list(bitpacking.encode_int_with_limits(value, limits)))

    # Assert
    assert result == expected


@pytest.fixture(
    params=[
        (False, (0, 2)),
        (True, (1, 2)),
    ],
    name="bool_fixture")
def _bool_fixture(request):
    return request.param[0], request.param[1]


def test_encode_bool(bool_fixture):
    # Setup
    value, encoded = bool_fixture

    # Run
    result = list(bitpacking.encode_bool(value))

    # Assert
    assert result == [encoded]


def test_decode_bool(bool_fixture):
    # Setup
    value, encoded = bool_fixture
    decoder = MagicMock()
    decoder.decode_single.return_value = encoded[0]

    # Run
    result = bitpacking.decode_bool(decoder)

    # Assert
    decoder.decode_single.assert_called_once_with(encoded[1])
    assert result == value


@pytest.mark.parametrize(["value", "metadata"], [
    (0.0, {"min": 0.0, "max": 1.0, "precision": 1}),
    (0.0, {"min": -1.0, "max": 1.0, "precision": 1}),
    (-0.5, {"min": -1.0, "max": 1.0, "precision": 1}),
    (1.0, {"min": 0.0, "max": 1.0, "precision": 1}),
    (1.0, {"min": 0.0, "max": 1.0, "precision": 2}),
])
def test_round_trip_float(value: float, metadata: dict):
    result = bitpacking.round_trip(bitpacking.BitPackFloat(value), metadata)
    assert result == value


@pytest.mark.parametrize(["elements", "array"], [
    ([], [10, 20]),
    ([10], [10, 20]),
    ([10, 20], [10, 20]),
    ([10, 20], [10, 20, 30]),
    ([10, 20], [10, 20, 30, 50]),
    (list(range(15)), list(range(100))),
    ([x * 2 for x in range(150)], list(range(300))),
])
def test_sorted_array_elements_round_trip(elements, array):
    generator = bitpacking.pack_sorted_array_elements(elements, array)
    b = bitpacking._pack_encode_results(list(generator))
    decoder = bitpacking.BitPackDecoder(b)

    decoded_elements = bitpacking.decode_sorted_array_elements(decoder, array)

    assert elements == decoded_elements


@pytest.mark.parametrize(["elements", "array", "expected_size"], [
    ([], [], 0),
    ([], range(100), 8),
    ([90], range(100), 18),
    (range(100), range(100), 8),
    (range(100), range(300), 219),
    (list(range(100)) + list(range(200, 300)), range(300), 318),
    (range(200), range(300), 120),
    (range(200, 300), range(300), 120),
    ([x * 2 for x in range(150)], range(300), 458),
    ([x * 3 for x in range(100)], range(300), 310),
])
def test_sorted_array_elements_size(elements, array, expected_size):
    count = 0
    for _, size in bitpacking.pack_sorted_array_elements(list(elements), list(array)):
        count += bitpacking._bits_for_number(size)
    assert count == expected_size


def test_pack_array_element_missing():
    with pytest.raises(ValueError):
        list(bitpacking.pack_array_element(5, [10, 25]))


def test_pack_array_element_single():
    assert len(list(bitpacking.pack_array_element("x", ["x"]))) == 0


@pytest.mark.parametrize(["element", "array"], [
    (10, [10, 20]),
    ("x", [10, "x", 20]),
    ("x", ["x"]),
])
def test_array_elements_round_trip(element, array):
    generator = bitpacking.pack_array_element(element, array)
    b = bitpacking._pack_encode_results(list(generator))
    decoder = bitpacking.BitPackDecoder(b)

    decoded_element = decoder.decode_element(array)

    assert element == decoded_element


class BitPackValueUsingReference(bitpacking.BitPackValue):
    value: int

    def __init__(self, x):
        self.value = x

    def bit_pack_encode(self, metadata) -> Iterator[Tuple[int, int]]:
        reference: BitPackValueUsingReference = metadata["reference"]
        yield self.value - reference.value, 128

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder, metadata):
        reference: BitPackValueUsingReference = metadata["reference"]
        value = decoder.decode_single(128) + reference.value
        return BitPackValueUsingReference(value)

    def __eq__(self, other):
        return self.value == other.value


@dataclasses.dataclass(frozen=True)
class DataclassForTest(bitpacking.BitPackDataclass):
    uses_reference: BitPackValueUsingReference


@pytest.mark.parametrize(["value", "reference"], [
    (10, 5),
    (20, 5),
    (50, 5),
])
def test_round_trip_dataclass_for_test(value, reference):
    data = DataclassForTest(BitPackValueUsingReference(value))
    ref = DataclassForTest(BitPackValueUsingReference(reference))

    result = bitpacking.round_trip(data, {"reference": ref})
    assert result == data
