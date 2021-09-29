import pytest

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder
from randovania.games.game import RandovaniaGame
from randovania.layout.base.trick_level import LayoutTrickLevel
from randovania.layout.base.trick_level_configuration import TrickLevelConfiguration


@pytest.fixture(
    params=[
        {"encoded": b'\x00\x00', "bit_count": 15, "json": {"minimal_logic": False, "specific_levels": {}}},
        {"encoded": b'\x80', "bit_count": 1, "json": {"minimal_logic": True, "specific_levels": {}}},
        {"encoded": b'X\x00\x00', "bit_count": 18, "json": {
            "minimal_logic": False, "specific_levels": {"Dash": "expert"}}},
        {"encoded": b'f3\x00\x00', "bit_count": 27, "json": {"minimal_logic": False, "specific_levels": {
            i: "hypermode"
            for i in ["Dash", "BombJump", "Movement", "BSJ"]
        }}},
    ],
    name="trick_level_data")
def _trick_level_data(request, mocker, echoes_game_description):
    tricks = echoes_game_description.resource_database.trick[:14]
    mocker.patch("randovania.layout.base.trick_level_configuration._all_tricks", return_value=tricks)
    return (request.param["encoded"], request.param["bit_count"],
            TrickLevelConfiguration.from_json(request.param["json"], game=RandovaniaGame.METROID_PRIME_ECHOES))


def test_decode(trick_level_data):
    # Setup
    data, _, expected = trick_level_data

    # Run
    decoder = BitPackDecoder(data)
    result = TrickLevelConfiguration.bit_pack_unpack(decoder, {
        "reference": TrickLevelConfiguration(False, {}, RandovaniaGame.METROID_PRIME_ECHOES),
    })

    # Assert
    assert result == expected


def test_encode(trick_level_data):
    expected_bytes, expected_bit_count, value = trick_level_data

    # Run
    result, bit_count = bitpacking.pack_results_and_bit_count(value.bit_pack_encode({}))

    # Assert
    assert result == expected_bytes
    assert bit_count == expected_bit_count


def test_encode_no_tricks_are_removed():
    from_json = TrickLevelConfiguration.from_json({"minimal_logic": False, "specific_levels": {"Dash": "disabled"}},
                                                  game=RandovaniaGame.METROID_PRIME_ECHOES)

    encoded, byte_count = bitpacking.pack_results_and_bit_count(from_json.bit_pack_encode({}))

    assert encoded == b'\x00\x00\x00\x00'
    assert byte_count == 26

    decoder = BitPackDecoder(encoded)
    decoded = TrickLevelConfiguration.bit_pack_unpack(
        decoder, {"reference": TrickLevelConfiguration(False, {}, RandovaniaGame.METROID_PRIME_ECHOES), })

    assert decoded.specific_levels == {}


def test_set_level_for_trick_remove(echoes_resource_database):
    trick = echoes_resource_database.trick[0]
    config = TrickLevelConfiguration(False, {}, RandovaniaGame.METROID_PRIME_ECHOES)

    assert config.level_for_trick(trick) == LayoutTrickLevel.DISABLED

    config = config.set_level_for_trick(trick, LayoutTrickLevel.ADVANCED)
    assert config.level_for_trick(trick) == LayoutTrickLevel.ADVANCED

    config = config.set_level_for_trick(trick, LayoutTrickLevel.DISABLED)
    assert config.level_for_trick(trick) == LayoutTrickLevel.DISABLED


def test_pretty_description_minimal_logic():
    config = TrickLevelConfiguration(True, {}, RandovaniaGame.METROID_PRIME_ECHOES)
    assert config.pretty_description == "Minimal Logic"


@pytest.mark.parametrize(["levels", "expected"], [
    ({}, "All tricks disabled"),
    ({i: LayoutTrickLevel.HYPERMODE for i in ["Dash", "BombJump", "Movement", "BSJ"]},
     "Enabled tricks: 21 at Disabled, 4 at Hypermode"),
    ({"Dash": LayoutTrickLevel.HYPERMODE, "BombJump": LayoutTrickLevel.HYPERMODE,
      "AirUnderwater": LayoutTrickLevel.ADVANCED},
     "Enabled tricks: 22 at Disabled, Air Underwater at Advanced, 2 at Hypermode"),
])
def test_pretty_description_tricks_echoes(levels, expected):
    config = TrickLevelConfiguration(False, levels, RandovaniaGame.METROID_PRIME_ECHOES)
    assert config.pretty_description == expected
