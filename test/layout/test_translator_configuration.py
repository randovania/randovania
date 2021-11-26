import pytest

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder
from randovania.games.prime2.layout.translator_configuration import TranslatorConfiguration


@pytest.fixture(
    params=[
        {"encoded": b'\x00', "bit_count": 2, "json": {"translator_requirement": {}}},
        {"encoded": b'@', "bit_count": 2, "json": TranslatorConfiguration.default().with_vanilla_colors().as_json},
        {"encoded": b'\x80', "bit_count": 2, "json": TranslatorConfiguration.default().with_full_random().as_json},
        {"encoded": b'\xc0\x00\xc0\x81%$\xd8', "bit_count": 53, "json": {"translator_requirement": {
            'Temple Grounds/Temple Assembly Site/Translator Gate': "random"
        }}},
    ],
    name="translator_data")
def _translator_data(request):
    return request.param["encoded"], request.param["bit_count"], TranslatorConfiguration.from_json(
        request.param["json"])


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
            'Agon Wastes/Mining Plaza/Translator Gate': 'amber',
            'Agon Wastes/Mining Station A/Translator Gate': 'amber',
            'Great Temple/Temple Sanctuary/Transport A Translator Gate': 'emerald',
            'Great Temple/Temple Sanctuary/Transport B Translator Gate': 'violet',
            'Great Temple/Temple Sanctuary/Transport C Translator Gate': 'amber',
            'Sanctuary Fortress/Reactor Core/Translator Gate': 'cobalt',
            'Sanctuary Fortress/Sanctuary Temple/Translator Gate': 'cobalt',
            'Temple Grounds/GFMC Compound/Translator Gate': 'violet',
            'Temple Grounds/Hive Access Tunnel/Translator Gate': 'violet',
            'Temple Grounds/Hive Transport Area/Translator Gate': 'violet',
            'Temple Grounds/Industrial Site/Translator Gate': 'violet',
            'Temple Grounds/Meeting Grounds/Translator Gate': 'violet',
            'Temple Grounds/Path of Eyes/Translator Gate': 'amber',
            'Temple Grounds/Temple Assembly Site/Translator Gate': 'violet',
            'Torvus Bog/Great Bridge/Translator Gate': 'emerald',
            'Torvus Bog/Torvus Temple/Elevator Translator Scan': 'emerald',
            'Torvus Bog/Torvus Temple/Translator Gate': 'emerald',
        }
    }
