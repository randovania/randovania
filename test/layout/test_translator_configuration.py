import pytest

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder
from randovania.layout.prime2.translator_configuration import TranslatorConfiguration


@pytest.fixture(
    params=[
        {"encoded": b'\x00', "bit_count": 2, "json": {"translator_requirement": {}}},
        {"encoded": b'@', "bit_count": 2, "json": TranslatorConfiguration.default().with_vanilla_colors().as_json},
        {"encoded": b'\x80', "bit_count": 2, "json": TranslatorConfiguration.default().with_full_random().as_json},
        {"encoded": b'\xc0\x00\xc0\n%$\xd8', "bit_count": 53, "json": {"translator_requirement": {
            "5": "random"
        }}},
    ],
    name="translator_data")
def _translator_data(request):
    return request.param["encoded"], request.param["bit_count"], TranslatorConfiguration.from_json(request.param["json"])


def test_decode(translator_data):
    # Setup
    data, _, expected = translator_data

    # Run
    decoder = BitPackDecoder(data)
    result = TranslatorConfiguration.bit_pack_unpack(decoder, {})

    # Assert
    assert result == expected


def test_encode(translator_data):
    # Setup
    expected_bytes, expected_bit_count, value = translator_data

    # Run
    result, bit_count = bitpacking.pack_results_and_bit_count(value.bit_pack_encode({}))

    # Assert
    assert result == expected_bytes
    assert bit_count == expected_bit_count


def test_blank_from_json():
    blank = TranslatorConfiguration.from_json({"translator_requirement": {}})
    assert blank.as_json == {
        "translator_requirement": {
            '0': 'violet', '1': 'violet', '2': 'violet', '3': 'violet', '4': 'amber', '5': 'violet', '6': 'violet',
            '7': 'violet', '8': 'amber', '9': 'emerald', '10': 'amber', '11': 'amber', '12': 'emerald',
            '13': 'emerald', '14': 'emerald', '15': 'cobalt', '16': 'cobalt'
        }
    }
