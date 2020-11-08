import pytest

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder
from randovania.layout.trick_level import TrickLevelConfiguration


@pytest.fixture(
    params=[
        {"encoded": b'\x00\x00', "json": {"minimal_logic": False, "specific_levels": {}}},
        {"encoded": b'\x80\x00', "json": {"minimal_logic": True, "specific_levels": {}}},
        {"encoded": b'X\x00\x00', "json": {"minimal_logic": False, "specific_levels": {"Dash": "expert"}}},
        {"encoded": b'f3\x00\x00', "json": {"minimal_logic": False, "specific_levels": {
            i: "hypermode"
            for i in ["Dash", "BombJump", "Movement", "BSJ"]
        }}},
    ],
    name="configuration_with_data")
def _configuration_with_data(request, mocker, echoes_game_description):
    tricks = echoes_game_description.resource_database.trick[:14]
    mocker.patch("randovania.layout.trick_level._all_tricks", return_value=tricks)
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
    expected, value = configuration_with_data

    # Run
    result = bitpacking._pack_encode_results([
        (value_argument, value_format)
        for value_argument, value_format in value.bit_pack_encode({})
    ])

    # Assert
    assert result == expected


def test_encode_no_tricks_are_removed():
    from_json = TrickLevelConfiguration.from_json({"minimal_logic": False, "specific_levels": {"Dash": "no-tricks"}})

    encoded = bitpacking._pack_encode_results([
        (value_argument, value_format)
        for value_argument, value_format in from_json.bit_pack_encode({})
    ])

    assert encoded == b'\x00\x00\x00\x00'

    decoder = BitPackDecoder(encoded)
    decoded = TrickLevelConfiguration.bit_pack_unpack(decoder, {})

    assert decoded.specific_levels == {}
