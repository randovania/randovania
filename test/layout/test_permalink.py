import dataclasses
from unittest.mock import patch, MagicMock

import pytest

from randovania.layout.layout_configuration import LayoutElevators, LayoutSkyTempleKeyMode
from randovania.layout.permalink import Permalink
from randovania.layout.preset import Preset
from randovania.layout.trick_level import LayoutTrickLevel, TrickLevelConfiguration


@patch("randovania.layout.permalink._dictionary_byte_hash", autospec=True)
def test_encode(mock_dictionary_byte_hash: MagicMock, preset_manager):
    # Setup
    mock_dictionary_byte_hash.return_value = 120
    link = Permalink(
        seed_number=1000,
        spoiler=True,
        presets={0: preset_manager.default_preset},
    )

    # Run
    encoded = link.as_str

    # Assert
    mock_dictionary_byte_hash.assert_called_once_with(preset_manager.default_preset.layout_configuration.game_data)
    assert encoded == "oAAAfRQeABo="


@pytest.mark.parametrize("invalid", [
    "",
    "a",
    "x",
    "zz",
    "AAAAfRxALWmCI50gIQD",
    "AAAAfRxALxmCI50gIQDy"
])
def test_decode_invalid(invalid: str):
    with pytest.raises(ValueError):
        Permalink.from_str(invalid)


@pytest.mark.parametrize("spoiler", [False, True])
@pytest.mark.parametrize("patcher", [
    {},
    {
        "menu_mod": True,
        "warp_to_start": False,
    },
])
@pytest.mark.parametrize("layout", [
    {},
    {
        "trick_level_configuration": TrickLevelConfiguration(LayoutTrickLevel.HARD),
        "sky_temple_keys": LayoutSkyTempleKeyMode.ALL_GUARDIANS,
        "elevators": LayoutElevators.TWO_WAY_RANDOMIZED,
    },
])
def test_round_trip(spoiler: bool,
                    patcher: dict,
                    layout: dict,
                    preset_manager):
    # Setup
    preset = Preset(
        name="{} Custom".format(preset_manager.default_preset.name),
        description="A customized preset.",
        base_preset_name=preset_manager.default_preset.name,
        patcher_configuration=dataclasses.replace(preset_manager.default_preset.patcher_configuration, **patcher),
        layout_configuration=dataclasses.replace(preset_manager.default_preset.layout_configuration, **layout),
    )

    link = Permalink(
        seed_number=1000,
        spoiler=spoiler,
        presets={0: preset},
    )

    # Run
    after = Permalink.from_str(link.as_str)

    # Assert
    assert link == after


@pytest.mark.parametrize(["permalink", "version"], [
    ("AAAAfR5QLERzIpgS4ICCAHw=", 0),
    ("EAAAfReObArRHMClxLYgIIA+", 1),
    ("MAAAfReKeBWiOYFLiWxAQQDk", 3),
])
def test_decode_old_version(permalink: str, version: int):
    with pytest.raises(ValueError) as exp:
        Permalink.from_str(permalink)
    assert str(exp.value) == ("Given permalink has version {}, but this Randovania "
                              "support only permalink of version {}.".format(version, Permalink.current_version()))


@patch("randovania.layout.permalink._dictionary_byte_hash", autospec=True)
def test_decode(mock_dictionary_byte_hash: MagicMock, preset_manager):
    mock_dictionary_byte_hash.return_value = 120
    # We're mocking the database hash to avoid breaking tests every single time we change the database

    # This test should break whenever we change how permalinks are created
    # When this happens, we must bump the permalink version and change the tests
    encoded = "oAAAfRQeABo="

    expected = Permalink(
        seed_number=1000,
        spoiler=True,
        presets={0: preset_manager.default_preset},
    )

    # Uncomment this line to quickly get the new encoded permalink
    # assert expected.as_str == ""
    # print(expected.as_str)

    # Run
    link = Permalink.from_str(encoded)

    # Assert
    assert link == expected


@pytest.mark.parametrize(["encoded", "num_players"], [
    ("oAAAfRUggB0=", 1),
    ("oAAAfRgBIKB2", 2),
    ("oAAAfRghIL/gbQ==", 10),
])
@patch("randovania.layout.layout_configuration.LayoutConfiguration.bit_pack_unpack")
@patch("randovania.layout.patcher_configuration.PatcherConfiguration.bit_pack_unpack")
def test_decode_mock_other(mock_packer_unpack: MagicMock,
                           mock_layout_unpack: MagicMock,
                           preset_manager,
                           encoded,
                           num_players,
                           ):
    patcher_configuration = mock_packer_unpack.return_value
    layout_configuration = mock_layout_unpack.return_value
    preset = Preset(
        name="{} Custom".format(preset_manager.default_preset.name),
        description="A customized preset.",
        base_preset_name=preset_manager.default_preset.name,
        patcher_configuration=patcher_configuration,
        layout_configuration=layout_configuration,
    )

    expected = Permalink(
        seed_number=1000,
        spoiler=True,
        presets={i: preset for i in range(num_players)},
    )
    patcher_configuration.bit_pack_encode.return_value = []
    layout_configuration.bit_pack_encode.return_value = []
    mock_layout_unpack.return_value.game_data = {"test": True}

    # Uncomment this line to quickly get the new encoded permalink
    # assert expected.as_str == ""
    # print(expected.as_str)

    # Run
    round_trip = expected.as_str
    link = Permalink.from_str(encoded)

    # Assert
    assert link == expected
    assert encoded == round_trip
    mock_packer_unpack.assert_called_once()
    mock_layout_unpack.assert_called_once()
    patcher_configuration.bit_pack_encode.assert_called_once_with(
        {"reference": preset_manager.default_preset.patcher_configuration})
    layout_configuration.bit_pack_encode.assert_called_once_with(
        {"reference": preset_manager.default_preset.layout_configuration})


@patch("randovania.layout.permalink.Permalink.bit_pack_encode", autospec=True)
def test_permalink_as_str_caches(mock_bit_pack_encode: MagicMock,
                                 preset_manager):
    # Setup
    mock_bit_pack_encode.return_value = []
    link = Permalink(
        seed_number=1000,
        spoiler=True,
        presets={0: preset_manager.default_preset},
    )

    # Run
    str1 = link.as_str
    str2 = link.as_str

    # Assert
    assert str1 == "Lg=="
    assert str1 == str2
    assert str2 == object.__getattribute__(link, "__cached_as_str")
    mock_bit_pack_encode.assert_called_once_with(link, {})
