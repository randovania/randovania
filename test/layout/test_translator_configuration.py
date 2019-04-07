import pytest

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder
from randovania.layout.translator_configuration import TranslatorConfiguration


@pytest.fixture(
    params=[
        {"encoded": b'\x00', "json": {"translator_requirement": {}}},
        {"encoded": b'@', "json": TranslatorConfiguration.vanilla_colors().as_json},
        {"encoded": b'\x80', "json": TranslatorConfiguration.full_random().as_json},
        {"encoded": b'\xc0\x00\xc0\n%$\xd8', "json": {"translator_requirement": {
            "5": "random"
        }}},
    ],
    name="configuration_with_data")
def _configuration_with_data(request):
    return request.param["encoded"], TranslatorConfiguration.from_json(request.param["json"])


def test_decode(configuration_with_data):
    # Setup
    data, expected = configuration_with_data

    # Run
    decoder = BitPackDecoder(data)
    result = TranslatorConfiguration.bit_pack_unpack(decoder)

    # Assert
    assert result == expected


def test_encode(configuration_with_data):
    # Setup
    expected, value = configuration_with_data

    # Run
    result = bitpacking._pack_encode_results([
        (value_argument, value_format)
        for value_argument, value_format in value.bit_pack_encode()
    ])

    # Assert
    assert result == expected


def test_blank_from_json():
    blank = TranslatorConfiguration.from_json({"translator_requirement": {}})
    assert blank.as_json == {"translator_requirement": {}}
