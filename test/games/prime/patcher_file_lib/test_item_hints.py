from __future__ import annotations

import dataclasses
import random
from unittest.mock import MagicMock

import pytest

from randovania.exporter.hints.hint_exporter import HintExporter
from randovania.game_description.assignment import PickupTarget
from randovania.game_description.db.area import Area
from randovania.game_description.db.area_identifier import AreaIdentifier
from randovania.game_description.db.hint_node import HintNode
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.game_description.db.pickup_node import PickupNode
from randovania.game_description.db.region import Region
from randovania.game_description.db.region_list import RegionList
from randovania.game_description.hint import (
    HintDarkTemple,
    HintItemPrecision,
    HintLocationPrecision,
    HintRelativeAreaName,
    JokeHint,
    LocationHint,
    PrecisionPair,
    RedTempleHint,
    RelativeDataArea,
    RelativeDataItem,
)
from randovania.game_description.requirements.base import Requirement
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.prime2.exporter import hints
from randovania.games.prime2.exporter.hint_namer import EchoesHintNamer
from randovania.games.prime2.patcher import echoes_items
from randovania.interface_common.players_configuration import PlayersConfiguration


@pytest.fixture
def players_config() -> PlayersConfiguration:
    return PlayersConfiguration(
        player_index=0,
        player_names={0: "Player 1"},
    )


def _create_region_list(asset_id: int, pickup_index: PickupIndex):
    nc = NodeIdentifier.create

    hint_node = HintNode(
        nc("World", "Area", "Logbook A"),
        0,
        True,
        None,
        "",
        ("default",),
        {"string_asset_id": asset_id},
        False,
        None,
        Requirement.trivial(),
    )
    pickup_node = PickupNode(
        nc("World", "Area", "Pickup Node"), 1, True, None, "", ("default",), {}, False, pickup_index, True
    )

    region_list = RegionList(
        [
            Region(
                "World",
                [
                    Area("Area", [hint_node, pickup_node], {}, {}),
                    Area(
                        "Other Area",
                        [
                            PickupNode(
                                nc("World", "Other Area", f"Pickup {i}"),
                                2 + i,
                                True,
                                None,
                                "",
                                ("default",),
                                {},
                                False,
                                PickupIndex(i),
                                True,
                            )
                            for i in range(pickup_index.index)
                        ],
                        {},
                        {},
                    ),
                ],
                {},
            ),
        ]
    )

    return hint_node, pickup_node, region_list


@pytest.fixture
def echoes_hint_exporter(echoes_game_patches, players_config) -> HintExporter:
    namer = EchoesHintNamer({0: echoes_game_patches}, players_config)
    return HintExporter(namer, random.Random(0), ["A Joke"])


def test_create_hints_nothing(echoes_game_patches, players_config):
    # Setup
    asset_id = 1000
    pickup_index = PickupIndex(0)

    hint_node, _, region_list = _create_region_list(asset_id, pickup_index)

    patches = dataclasses.replace(
        echoes_game_patches,
        hints={
            hint_node.identifier: LocationHint(
                PrecisionPair(HintLocationPrecision.DETAILED, HintItemPrecision.DETAILED, include_owner=False),
                pickup_index,
            )
        },
    )
    rng = MagicMock()
    namer = EchoesHintNamer({0: patches}, players_config)

    # Run
    result = hints.create_patches_hints({0: patches}, players_config, region_list, namer, rng)

    # Assert
    message = (
        "An &push;&main-color=#FF6705B3;Energy Transfer Module&pop; can be found in "
        "&push;&main-color=#FF3333;Temple Grounds - Hive Chamber A&pop;."
    )
    assert result == [{"asset_id": asset_id, "strings": [message, "", message]}]


def test_create_hints_item_joke(echoes_game_patches, players_config):
    # Setup
    asset_id = 1000
    hint_node, _, region_list = _create_region_list(asset_id, PickupIndex(50))

    patches = dataclasses.replace(echoes_game_patches, hints={hint_node.identifier: JokeHint()})
    rng = MagicMock()
    namer = EchoesHintNamer({0: patches}, players_config)

    # Run
    result = hints.create_patches_hints({0: patches}, players_config, region_list, namer, rng)

    # Assert
    joke = "Your current Chozo Battle Suit version is SA1-4468-VM6-P."
    message = f"&push;&main-color=#45F731;{joke}&pop;"
    assert result[0]["strings"][0] == message
    assert result == [{"asset_id": asset_id, "strings": [message, "", message]}]


@pytest.mark.parametrize(
    ("indices", "expected_message"),
    [
        (
            (0, 1, 2),
            "The keys to &push;&main-color=#FF6705B3;Dark Torvus Temple&pop; can "
            "all be found in &push;&main-color=#FF3333;Temple Grounds&pop;.",
        ),
        (
            (0, 1, 118),
            "The keys to &push;&main-color=#FF6705B3;Dark Torvus Temple&pop; can "
            "be found in &push;&main-color=#FF3333;Sanctuary Fortress&pop; "
            "and &push;&main-color=#FF3333;Temple Grounds&pop;.",
        ),
        (
            (0, 41, 118),
            "The keys to &push;&main-color=#FF6705B3;Dark Torvus Temple&pop; can "
            "be found in &push;&main-color=#FF3333;Dark Agon Wastes&pop;, "
            "&push;&main-color=#FF3333;Sanctuary Fortress&pop; and "
            "&push;&main-color=#FF3333;Temple Grounds&pop;.",
        ),
    ],
)
def test_create_hints_item_dark_temple_keys(
    echoes_game_patches,
    players_config,
    echoes_game_description,
    blank_pickup,
    indices,
    expected_message,
    preset_manager,
):
    # Setup
    db = echoes_game_description.resource_database
    keys = [
        (PickupIndex(index), dataclasses.replace(blank_pickup, progression=((db.get_item(item), 1),)))
        for index, item in zip(indices, echoes_items.DARK_TEMPLE_KEY_ITEMS[1])
    ]

    patches = dataclasses.replace(
        echoes_game_patches,
        configuration=preset_manager.default_preset_for_game(db.game_enum).get_preset().configuration,
        pickup_assignment={pickup_index: PickupTarget(key, 0) for pickup_index, key in keys},
    )

    hint = RedTempleHint(dark_temple=HintDarkTemple.TORVUS_BOG)

    namer = EchoesHintNamer({0: patches}, players_config)
    exporter = HintExporter(namer, random.Random(0), ["A Joke"])

    # Run
    result = exporter.create_message_for_hint(hint, True)

    # Assert
    assert result == expected_message


def test_create_hints_item_dark_temple_keys_cross_game(
    blank_pickup,
    echoes_resource_database,
    echoes_game_patches,
    default_echoes_configuration,
    prime_game_patches,
    default_prime_configuration,
):
    # Setup
    players_config = PlayersConfiguration(
        player_index=0,
        player_names={
            0: "Player 1",
            1: "Player 2",
        },
    )

    keys = [
        dataclasses.replace(blank_pickup, progression=((echoes_resource_database.get_item(item), 1),))
        for item in echoes_items.DARK_TEMPLE_KEY_ITEMS[1]
    ]

    echoes_patches = dataclasses.replace(
        echoes_game_patches,
        configuration=default_echoes_configuration,
        pickup_assignment={
            PickupIndex(14): PickupTarget(keys[0], 0),
            PickupIndex(80): PickupTarget(keys[2], 0),
        },
    )
    prime_patches = dataclasses.replace(
        prime_game_patches,
        configuration=default_prime_configuration,
        pickup_assignment={
            PickupIndex(23): PickupTarget(keys[1], 0),
        },
    )

    hint = RedTempleHint(dark_temple=HintDarkTemple.TORVUS_BOG)

    namer = EchoesHintNamer({0: echoes_patches, 1: prime_patches}, players_config)
    exporter = HintExporter(namer, random.Random(0), ["A Joke"])

    # Run
    result = exporter.create_message_for_hint(hint, True)

    # Assert
    assert result == (
        "The keys to &push;&main-color=#FF6705B3;Dark Torvus Temple&pop; can be found "
        "in &push;&main-color=#FF3333;Chozo Ruins&pop;, "
        "&push;&main-color=#FF3333;Dark Torvus Bog&pop; and "
        "&push;&main-color=#FF3333;Temple Grounds&pop;."
    )


def test_create_message_for_hint_dark_temple_no_keys(empty_patches, players_config, echoes_hint_exporter):
    # Setup
    hint = RedTempleHint(dark_temple=HintDarkTemple.TORVUS_BOG)
    echoes_hint_exporter.namer.all_patches = {0: empty_patches}

    # Run
    result = echoes_hint_exporter.create_message_for_hint(hint, True)

    # Assert
    assert result == "The keys to &push;&main-color=#FF6705B3;Dark Torvus Temple&pop; are nowhere to be found."


@pytest.mark.parametrize(
    "item",
    [
        (HintItemPrecision.DETAILED, "The", "&push;&main-color=#FF6705B3;Blank Pickup&pop;"),
    ],
)
@pytest.mark.parametrize(
    "location",
    [
        (HintLocationPrecision.DETAILED, "&push;&main-color=#FF3333;Dark Agon Wastes - Doomed Entry&pop;"),
        (HintLocationPrecision.REGION_ONLY, "&push;&main-color=#FF3333;Dark Agon Wastes&pop;"),
    ],
)
@pytest.mark.parametrize("owner", [False, True])
@pytest.mark.parametrize("is_multiworld", [False, True])
def test_create_hints_item_location(echoes_game_patches, blank_pickup, item, location, owner, is_multiworld):
    # Setup
    asset_id = 1000
    pickup_index = PickupIndex(50)
    hint_node, _, region_list = _create_region_list(asset_id, pickup_index)

    players_config = PlayersConfiguration(
        player_index=0,
        player_names={i: f"Player {i + 1}" for i in range(int(is_multiworld) + 1)},
    )
    location_precision, determiner, item_name = item
    if owner and is_multiworld:
        determiner = "&push;&main-color=#d4cc33;Player 1&pop;'s"

    patches = dataclasses.replace(
        echoes_game_patches,
        pickup_assignment={
            pickup_index: PickupTarget(blank_pickup, 0),
        },
        hints={
            hint_node.identifier: LocationHint(
                PrecisionPair(location[0], location_precision, include_owner=owner),
                pickup_index,
            )
        },
    )
    rng = MagicMock()
    namer = EchoesHintNamer({0: patches}, players_config)

    # Run
    result = hints.create_patches_hints({0: patches}, players_config, region_list, namer, rng)

    # Assert
    message = f"{determiner} {item_name} can be found in {location[1]}."
    # message = "The Flying Ing Cache in {} contains {}.".format(location[1], item[1])
    assert result[0]["strings"][0] == message
    assert result == [{"asset_id": asset_id, "strings": [message, "", message]}]


@pytest.mark.parametrize(
    "pickup_index_and_guardian",
    [
        (PickupIndex(43), "&push;&main-color=#FF3333;Amorbis&pop;"),
        (PickupIndex(79), "&push;&main-color=#FF3333;Chykka&pop;"),
        (PickupIndex(115), "&push;&main-color=#FF3333;Quadraxis&pop;"),
    ],
)
@pytest.mark.parametrize(
    "item",
    [
        (HintItemPrecision.DETAILED, "the &push;&main-color=#FF6705B3;Blank Pickup&pop;"),
    ],
)
def test_create_hints_guardians(
    echoes_game_patches,
    pickup_index_and_guardian,
    blank_pickup,
    item,
    players_config,
):
    # Setup
    asset_id = 1000
    pickup_index, guardian = pickup_index_and_guardian

    hint_node, _, region_list = _create_region_list(asset_id, pickup_index)

    patches = dataclasses.replace(
        echoes_game_patches,
        pickup_assignment={
            pickup_index: PickupTarget(blank_pickup, 0),
        },
        hints={
            hint_node.identifier: LocationHint(
                PrecisionPair(
                    echoes_game_patches.game.hint_feature_database["specific_hint_guardian"],
                    item[0],
                    include_owner=False,
                ),
                pickup_index,
            )
        },
    )
    rng = MagicMock()
    namer = EchoesHintNamer({0: patches}, players_config)

    # Run
    result = hints.create_patches_hints({0: patches}, players_config, region_list, namer, rng)

    # Assert
    message = f"{guardian} is guarding {item[1]}."
    assert result == [{"asset_id": asset_id, "strings": [message, "", message]}]


@pytest.mark.parametrize(
    "item",
    [
        (HintItemPrecision.DETAILED, "the &push;&main-color=#FF6705B3;Blank Pickup&pop;"),
    ],
)
def test_create_hints_light_suit_location(echoes_game_patches, players_config, blank_pickup, item):
    # Setup
    asset_id = 1000
    pickup_index = PickupIndex(50)

    hint_node, _, region_list = _create_region_list(asset_id, pickup_index)

    patches = dataclasses.replace(
        echoes_game_patches,
        pickup_assignment={
            pickup_index: PickupTarget(blank_pickup, 0),
        },
        hints={
            hint_node.identifier: LocationHint(
                PrecisionPair(
                    echoes_game_patches.game.hint_feature_database["specific_hint_2mos"], item[0], include_owner=False
                ),
                pickup_index,
            )
        },
    )
    rng = MagicMock()
    namer = EchoesHintNamer({0: patches}, players_config)

    # Run
    result = hints.create_patches_hints({0: patches}, players_config, region_list, namer, rng)

    # Assert
    message = f"U-Mos's reward for returning the Sanctuary energy is {item[1]}."
    assert result == [{"asset_id": asset_id, "strings": [message, "", message]}]


@pytest.mark.parametrize(
    ("reference_precision", "reference_name"),
    [
        (HintItemPrecision.DETAILED, "the Reference Pickup"),
    ],
)
@pytest.mark.parametrize(
    ("distance_precise", "distance_text"),
    [
        (1, "up to"),
        (0, "up to"),
        (None, "exactly"),
    ],
)
def test_create_message_for_hint_relative_item(
    echoes_game_patches,
    blank_pickup,
    players_config,
    distance_precise,
    distance_text,
    reference_precision,
    reference_name,
):
    patches = echoes_game_patches.assign_new_pickups(
        [
            (PickupIndex(5), PickupTarget(blank_pickup, 0)),
            (PickupIndex(15), PickupTarget(dataclasses.replace(blank_pickup, name="Reference Pickup"), 0)),
        ]
    )

    hint = LocationHint(
        PrecisionPair(
            HintLocationPrecision.RELATIVE_TO_INDEX,
            HintItemPrecision.DETAILED,
            include_owner=False,
            relative=RelativeDataItem(distance_precise, PickupIndex(15), reference_precision),
        ),
        PickupIndex(5),
    )

    namer = EchoesHintNamer({0: patches}, players_config)
    exporter = HintExporter(namer, random.Random(0), ["A Joke"])

    # Run
    result = exporter.create_message_for_hint(hint, True)

    # Assert
    assert result == (
        f"The &push;&main-color=#FF6705B3;Blank Pickup&pop; can be found "
        f"&push;&main-color=#FF3333;{distance_text} {7 + (distance_precise or 0)} "
        f"rooms&pop; away from {reference_name}."
    )


@pytest.mark.parametrize(
    ("offset", "distance_text"),
    [
        (2, "up to"),
        (None, "exactly"),
    ],
)
def test_create_message_for_hint_relative_area(
    echoes_game_patches, blank_pickup, players_config, echoes_hint_exporter, offset, distance_text
):
    patches = echoes_game_patches.assign_new_pickups(
        [
            (PickupIndex(5), PickupTarget(blank_pickup, 0)),
        ]
    )

    hint = LocationHint(
        PrecisionPair(
            HintLocationPrecision.RELATIVE_TO_AREA,
            HintItemPrecision.DETAILED,
            include_owner=False,
            relative=RelativeDataArea(offset, AreaIdentifier("Torvus Bog", "Great Bridge"), HintRelativeAreaName.NAME),
        ),
        PickupIndex(5),
    )

    namer = EchoesHintNamer({0: patches}, players_config)
    exporter = HintExporter(namer, random.Random(0), ["A Joke"])

    # Run
    result = exporter.create_message_for_hint(hint, True)

    # Assert
    assert result == (
        f"The &push;&main-color=#FF6705B3;Blank Pickup&pop; can be found "
        f"&push;&main-color=#FF3333;{distance_text} {10 + (offset or 0)} rooms&pop; away from "
        f"Torvus Bog - Great Bridge."
    )


@pytest.mark.parametrize("item_feature_id", ["suit", "beam"])
@pytest.mark.parametrize("loc_feature_id", ["half_pipe", "boss"])
def test_create_message_for_featural_hint(
    item_feature_id: str,
    loc_feature_id: str,
    echoes_game_patches,
    blank_pickup,
    echoes_pickup_database,
    echoes_game_description,
    players_config,
):
    patches = echoes_game_patches.assign_new_pickups(
        [
            (PickupIndex(5), PickupTarget(blank_pickup, 0)),
        ]
    )

    namer = EchoesHintNamer({0: patches}, players_config)
    exporter = HintExporter(namer, random.Random(0), ["A Joke"])

    loc_feature = echoes_game_description.hint_feature_database[loc_feature_id]
    item_feature = echoes_pickup_database.pickup_categories[item_feature_id]
    hint = LocationHint(
        PrecisionPair(
            loc_feature,
            item_feature,
            include_owner=False,
        ),
        PickupIndex(5),
    )

    # Run
    result = exporter.create_message_for_hint(hint, True)

    assert result == (
        f"{item_feature.hint_details[0].capitalize()}"
        f"&push;&main-color=#FF6705B3;{item_feature.hint_details[1]}&pop; "
        f"can be found &push;&main-color=#FF3333;{loc_feature.hint_details[1]}&pop;."
    )
