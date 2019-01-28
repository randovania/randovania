from unittest.mock import patch, MagicMock

import pytest

from randovania.layout.layout_configuration import LayoutConfiguration, LayoutTrickLevel, LayoutRandomizedFlag, \
    LayoutEnabledFlag, LayoutSkyTempleKeyMode
from randovania.layout.patcher_configuration import PatcherConfiguration
from randovania.layout.permalink import Permalink
from randovania.layout.starting_location import StartingLocation
from randovania.layout.starting_resources import StartingResources


@patch("randovania.layout.permalink._dictionary_byte_hash", autospec=True)
def test_encode(mock_dictionary_byte_hash: MagicMock):
    # Setup
    mock_dictionary_byte_hash.return_value = 120
    link = Permalink(
        seed_number=1000,
        spoiler=True,
        patcher_configuration=PatcherConfiguration.default(),
        layout_configuration=LayoutConfiguration.default(),
    )

    # Run
    encoded = link.as_str

    # Assert
    mock_dictionary_byte_hash.assert_called_once_with(link.layout_configuration.game_data)
    assert encoded == "EAAAfReMYK4="


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
    PatcherConfiguration.default(),
    PatcherConfiguration(
        disable_hud_popup=False,
        menu_mod=True,
    ),
])
@pytest.mark.parametrize("layout", [
    LayoutConfiguration.default(),
    LayoutConfiguration.from_params(
        trick_level=LayoutTrickLevel.HARD,
        sky_temple_keys=LayoutSkyTempleKeyMode.FULLY_RANDOM,
        item_loss=LayoutEnabledFlag.ENABLED,
        elevators=LayoutRandomizedFlag.RANDOMIZED,
        pickup_quantities={
            "Missile Expansion": 10,
            "Light Suit": 9,
        },
        starting_location=StartingLocation.default(),
        starting_resources=StartingResources.default(),
    ),
])
def test_round_trip(spoiler: bool,
                    patcher: PatcherConfiguration,
                    layout: LayoutConfiguration):
    # Setup
    link = Permalink(
        seed_number=1000,
        spoiler=spoiler,
        patcher_configuration=patcher,
        layout_configuration=layout,
    )

    # Run
    after = Permalink.from_str(link.as_str)

    # Assert
    assert link == after


@pytest.mark.parametrize(["permalink", "version"], [
    ("AAAAfR5QLERzIpgS4ICCAHw=", 0),
])
def test_decode_old_version(permalink: str, version: int):
    with pytest.raises(ValueError) as exp:
        Permalink.from_str(permalink)
    assert str(exp.value) == ("Given permalink has version {}, but this Randovania "
                              "support only permalink of version {}.".format(version, Permalink.current_version()))


@patch("randovania.layout.permalink._dictionary_byte_hash", autospec=True)
def test_decode_v1(mock_dictionary_byte_hash: MagicMock):
    mock_dictionary_byte_hash.return_value = 120
    # We're mocking the database hash to avoid breaking tests every single time we change the database

    # This test should break whenever we change how permalinks are created
    # When this happens, we must bump the permalink version and change the tests
    encoded = "EAAAfReObArRHMClxLYgIIA+"

    expected = Permalink(
        seed_number=1000,
        spoiler=True,
        patcher_configuration=PatcherConfiguration(
            disable_hud_popup=True,
            menu_mod=True,
        ),
        layout_configuration=LayoutConfiguration.from_params(
            trick_level=LayoutTrickLevel.HARD,
            sky_temple_keys=LayoutSkyTempleKeyMode.FULLY_RANDOM,
            item_loss=LayoutEnabledFlag.ENABLED,
            elevators=LayoutRandomizedFlag.RANDOMIZED,
            pickup_quantities={
                "Missile Expansion": 10,
                "Light Suit": 9,
            },
            starting_location=StartingLocation.default(),
            starting_resources=StartingResources.default(),
        ),
    )

    # Uncomment this line to quickly get the new encoded permalink
    # assert expected.as_str == ""

    # Run
    link = Permalink.from_str(encoded)

    # Assert
    assert link == expected
