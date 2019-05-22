import pytest

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder
from randovania.layout.trick_level import TrickLevelConfiguration


@pytest.fixture(
    params=[
        {"encoded": b'`\x00\x00', "json": {"global_level": "normal", "specific_levels": {}}},
        {"encoded": b'\xc0\x00\x00', "json": {"global_level": "minimal-restrictions", "specific_levels": {}}},
        {"encoded": b'P\x00\x00', "json": {"global_level": "easy", "specific_levels": {0: "no-tricks"}}},
        {"encoded": b'{\xbb\xbb\xbb\xbb\xbb\xa0', "json": {"global_level": "normal", "specific_levels": {
            i: "hypermode"
            for i in range(12)
        }}},
    ],
    name="configuration_with_data")
def _configuration_with_data(request):
    return request.param["encoded"], TrickLevelConfiguration.from_json(request.param["json"])


def test_decode(configuration_with_data):
    # Setup
    data, expected = configuration_with_data

    # Run
    decoder = BitPackDecoder(data)
    result = TrickLevelConfiguration.bit_pack_unpack(decoder, {})

    # Assert
    assert result == expected


def test_encode(configuration_with_data):
    # Setup
    expected, value = configuration_with_data

    # Run
    result = bitpacking._pack_encode_results([
        (value_argument, value_format)
        for value_argument, value_format in value.bit_pack_encode({})
    ])

    # Assert
    assert result == expected
