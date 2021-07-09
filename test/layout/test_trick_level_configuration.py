import pytest

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder
from randovania.games.game import RandovaniaGame
from randovania.layout.base.trick_level import LayoutTrickLevel
from randovania.layout.base.trick_level_configuration import TrickLevelConfiguration


@pytest.fixture(
    params=[
        {"encoded": b'\x00\x00', "json": {"minimal_logic": False, "specific_levels": {}}},
        {"encoded": b'\x80', "json": {"minimal_logic": True, "specific_levels": {}}},
        {"encoded": b'X\x00\x00', "json": {"minimal_logic": False, "specific_levels": {"Dash": "expert"}}},
        {"encoded": b'f3\x00\x00', "json": {"minimal_logic": False, "specific_levels": {
            i: "hypermode"
            for i in ["Dash", "BombJump", "Movement", "BSJ"]
        }}},
    ],
    name="configuration_with_data")
def _configuration_with_data(request, mocker, echoes_game_description):
    tricks = echoes_game_description.resource_database.trick[:14]
    mocker.patch("randovania.layout.base.trick_level_configuration._all_tricks", return_value=tricks)
    return request.param["encoded"], TrickLevelConfiguration.from_json(request.param["json"],
                                                                       game=RandovaniaGame.METROID_PRIME_ECHOES)


def test_decode(configuration_with_data):
    # Setup
    data, expected = configuration_with_data

    # Run
    decoder = BitPackDecoder(data)
    result = TrickLevelConfiguration.bit_pack_unpack(decoder, {
        "reference": TrickLevelConfiguration(False, {}, RandovaniaGame.METROID_PRIME_ECHOES),
    })

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
    from_json = TrickLevelConfiguration.from_json({"minimal_logic": False, "specific_levels": {"Dash": "disabled"}},
                                                  game=RandovaniaGame.METROID_PRIME_ECHOES)

    encoded = bitpacking._pack_encode_results([
        (value_argument, value_format)
        for value_argument, value_format in from_json.bit_pack_encode({})
    ])

    assert encoded == b'\x00\x00\x00\x00'

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
    ({}, "All at Disabled"),
    ({i: LayoutTrickLevel.HYPERMODE for i in ["Dash", "BombJump", "Movement", "BSJ"]},
     "21 at Disabled, 4 at Hypermode"),
    ({"Dash": LayoutTrickLevel.HYPERMODE, "BombJump": LayoutTrickLevel.HYPERMODE,
      "AirUnderwater": LayoutTrickLevel.ADVANCED},
     "22 at Disabled, 1 at Advanced, 2 at Hypermode"),
])
def test_pretty_description_tricks_echoes(levels, expected):
    config = TrickLevelConfiguration(False, levels, RandovaniaGame.METROID_PRIME_ECHOES)
    assert config.pretty_description == expected

