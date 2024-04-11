from __future__ import annotations

import pytest

from randovania.exporter.hints.determiner import Determiner
from randovania.exporter.hints.hint_namer import PickupLocation
from randovania.exporter.hints.pickup_hint import PickupHint
from randovania.game_description.hint import Hint, HintItemPrecision, HintLocationPrecision, HintType, PrecisionPair
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.fusion.exporter.hint_namer import FusionHintNamer
from randovania.games.game import RandovaniaGame
from randovania.interface_common.players_configuration import PlayersConfiguration


@pytest.mark.parametrize(
    ("color"),
    [
        (True),
        (False),
    ],
)
def test_starting_resource(fusion_game_patches, default_fusion_configuration, color: bool):
    players = PlayersConfiguration(0, {0: "Player1"})
    namer = FusionHintNamer({0: fusion_game_patches}, players)
    expected = (
        "[COLOR=3]Screw Attack[/COLOR] has no need to be located."
        if color
        else "Screw Attack has no need to be located."
    )
    hint = namer.format_resource_is_starting(ItemResourceInfo(1, "Screw Attack", "ScrewAttack", 1), color)
    assert hint == expected


@pytest.mark.parametrize(
    ("color"),
    [
        (True),
        (False),
    ],
)
def test_guaranteed_resource(fusion_game_patches, default_fusion_configuration, color: bool):
    players = PlayersConfiguration(0, {0: "Player1"})
    namer = FusionHintNamer({0: fusion_game_patches}, players)
    expected = (
        "[COLOR=3]Screw Attack[/COLOR] " if color else "Screw Attack ",
        "is located in ",
        "[COLOR=1]Player1[/COLOR]'s " if color else "Player1's ",
        "[COLOR=2]Sector 2 (TRO) - Level 1 Security Room[/COLOR]."
        if color
        else "Sector 2 (TRO) - Level 1 Security Room.",
    )
    hint = namer.format_guaranteed_resource(
        ItemResourceInfo(1, "Screw Attack", "ScrewAttack", 1),
        "Player1",
        PickupLocation(RandovaniaGame.FUSION, PickupIndex(116)),
        False,
        color,
    )
    assert hint == "".join(expected)


@pytest.mark.parametrize(
    ("color"),
    [
        (True),
        (False),
    ],
)
def test_format_location_hint(fusion_game_patches, default_fusion_configuration, color: bool):
    players = PlayersConfiguration(0, {0: "Player1"})
    namer = FusionHintNamer({0: fusion_game_patches}, players)
    expected = (
        "[COLOR=1]" if color else "",
        "Player1",
        "[/COLOR]'s " if color else "'s ",
        "[COLOR=3]" if color else "",
        "Screw Attack",
        "[/COLOR] " if color else " ",
        "can be found in ",
        "[COLOR=2]" if color else "",
        "Sector 2 (TRO) - Level 1 Security Room",
        "[/COLOR].\n" if color else ".\n",
    )
    hint = namer.format_location_hint(
        RandovaniaGame.FUSION,
        PickupHint(Determiner("item", True), "Player1", "Screw Attack"),
        Hint(
            HintType.LOCATION,
            PrecisionPair(HintLocationPrecision.DETAILED, HintItemPrecision.DETAILED, True),
            PickupIndex(116),
        ),
        color,
    )

    assert hint == "".join(expected)


@pytest.mark.parametrize(
    ("color"),
    [
        (True),
        (False),
    ],
)
def test_format_region(fusion_game_patches, default_fusion_configuration, color: bool):
    players = PlayersConfiguration(0, {0: "Player1"})
    namer = FusionHintNamer({0: fusion_game_patches}, players)
    location = PickupLocation(RandovaniaGame.FUSION, PickupIndex(116))
    expected = ("[COLOR=2]" if color else "", "Sector 2 (TRO)", "[/COLOR]" if color else "")
    hint = namer.format_region(location, color)
    assert hint == "".join(expected)


@pytest.mark.parametrize(
    ("with_region", "color"),
    [
        (True, True),
        (False, False),
    ],
)
def test_format_area(fusion_game_patches, default_fusion_configuration, with_region: bool, color: bool):
    players = PlayersConfiguration(0, {0: "Player1"})
    namer = FusionHintNamer({0: fusion_game_patches}, players)
    location = PickupLocation(RandovaniaGame.FUSION, PickupIndex(116))
    expected = (
        "[COLOR=2]" if color else "",
        "Sector 2 (TRO) - " if with_region else "",
        "Level 1 Security Room",
        "[/COLOR]" if color else "",
    )
    hint = namer.format_area(location, with_region, color)
    assert hint == "".join(expected)


@pytest.mark.parametrize(
    ("player", "color"),
    [
        ("Player1", True),
        ("Player2", False),
    ],
)
def test_format_player(fusion_game_patches, default_fusion_configuration, player: str, color: bool):
    expected = f"[COLOR=1]{player}[/COLOR]" if color else f"{player}"
    players = PlayersConfiguration(0, {0: player})
    namer = FusionHintNamer({0: fusion_game_patches}, players)
    hint = namer.format_player(player, color)
    assert hint == expected


@pytest.mark.parametrize(
    ("color"),
    [
        (True),
        (False),
    ],
)
def test_format_joke(fusion_game_patches, default_fusion_configuration, color: bool):
    expected = "[COLOR=4]This is a joke.[/COLOR]" if color else "This is a joke."
    players = PlayersConfiguration(0, {0: "Player1"})
    namer = FusionHintNamer({0: fusion_game_patches}, players)
    hint = namer.format_joke("This is a joke.", color)
    assert hint == expected
