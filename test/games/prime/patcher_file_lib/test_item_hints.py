import dataclasses
from unittest.mock import MagicMock

import pytest

from randovania.game_description.area import Area
from randovania.game_description.assignment import PickupTarget
from randovania.game_description.hint import Hint, HintType, HintLocationPrecision, HintItemPrecision, PrecisionPair
from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.node import LogbookNode, PickupNode
from randovania.game_description.resources.pickup_entry import PickupEntry, ConditionalResources
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.world import World
from randovania.game_description.world_list import WorldList
from randovania.games.prime.patcher_file_lib import item_hints


@pytest.fixture(name="pickup")
def _pickup() -> PickupEntry:
    return PickupEntry(
        name="Pickup",
        model_index=0,
        item_category=ItemCategory.MOVEMENT,
        resources=(
            ConditionalResources(None, None, ()),
        ),
    )


def _create_world_list(asset_id: int, pickup_index: PickupIndex):
    logbook_node = LogbookNode("Logbook A", True, 0, asset_id, None, None, None, None)
    pickup_node = PickupNode("Pickup Node", True, 1, pickup_index, True)

    world_list = WorldList([
        World("World", "Dark World", 5000, [
            Area("Area", False, 10000, 0, [logbook_node, pickup_node], {}),
        ]),
    ])

    return logbook_node, pickup_node, world_list


def test_create_hints_nothing(empty_patches):
    # Setup
    asset_id = 1000
    pickup_index = PickupIndex(50)

    logbook_node, _, world_list = _create_world_list(asset_id, pickup_index)

    patches = dataclasses.replace(
        empty_patches,
        hints={
            logbook_node.resource(): Hint(HintType.LOCATION,
                                          PrecisionPair.detailed(),
                                          pickup_index)
        })
    rng = MagicMock()

    # Run
    result = item_hints.create_hints(patches, world_list, rng)

    # Assert
    message = ("An &push;&main-color=#FF6705B3;Energy Transfer Module&pop; can be found in "
               "&push;&main-color=#FF3333;World - Area&pop;.")
    assert result == [
        {'asset_id': asset_id, 'strings': [message, '', message]}
    ]


@pytest.mark.parametrize("hint_type", [HintType.LOCATION, HintType.KEYBEARER])
@pytest.mark.parametrize("item", [
    (HintItemPrecision.DETAILED, "the &push;&main-color=#FF6705B3;Pickup&pop;"),
    (HintItemPrecision.PRECISE_CATEGORY, "a &push;&main-color=#FF6705B3;movement system&pop;"),
    (HintItemPrecision.GENERAL_CATEGORY, "a &push;&main-color=#FF6705B3;major upgrade&pop;"),
    (HintItemPrecision.WRONG_GAME, "the &push;&main-color=#45F731;X-Ray Visor (?)&pop;"),
])
@pytest.mark.parametrize("location", [
    (HintLocationPrecision.DETAILED, "&push;&main-color=#FF3333;World - Area&pop;"),
    (HintLocationPrecision.WORLD_ONLY, "&push;&main-color=#FF3333;World&pop;"),
    (HintLocationPrecision.WRONG_GAME, "&push;&main-color=#45F731;Tower (?)&pop;"),
])
def test_create_hints_item_detailed(hint_type, empty_patches, pickup, item, location):
    # Setup
    asset_id = 1000
    pickup_index = PickupIndex(50)

    logbook_node, _, world_list = _create_world_list(asset_id, pickup_index)

    patches = dataclasses.replace(
        empty_patches,
        pickup_assignment={
            pickup_index: PickupTarget(pickup, 0),
        },
        hints={
            logbook_node.resource(): Hint(hint_type,
                                          PrecisionPair(location[0], item[0]),
                                          pickup_index)
        })
    rng = MagicMock()

    # Run
    result = item_hints.create_hints(patches, world_list, rng)

    # Assert
    if location[0] == HintLocationPrecision.WRONG_GAME and item[0] == HintItemPrecision.WRONG_GAME:
        message = "&push;&main-color=#45F731;Warning! Dark Aether's atmosphere is dangerous!" \
                  " Energized Safe Zones don't last forever!&pop;"
    elif hint_type == HintType.LOCATION:
        message = "{} can be found in {}.".format(item[1][0].upper() + item[1][1:], location[1])
    elif hint_type == HintType.KEYBEARER:
        message = "The Flying Ing Cache in {} contains {}.".format(location[1], item[1])
    assert result == [{'asset_id': asset_id, 'strings': [message, '', message]}]

@pytest.mark.parametrize("pickup_index_and_guardian", [
    (PickupIndex(43), "&push;&main-color=#FF3333;Amorbis&pop;"),
    (PickupIndex(79), "&push;&main-color=#FF3333;Chykka&pop;"),
    (PickupIndex(115), "&push;&main-color=#FF3333;Quadraxis&pop;"),
])
@pytest.mark.parametrize("item", [
    (HintItemPrecision.DETAILED, "the &push;&main-color=#FF6705B3;Pickup&pop;"),
    (HintItemPrecision.PRECISE_CATEGORY, "a &push;&main-color=#FF6705B3;movement system&pop;"),
    (HintItemPrecision.GENERAL_CATEGORY, "a &push;&main-color=#FF6705B3;major upgrade&pop;"),
    (HintItemPrecision.WRONG_GAME, "the &push;&main-color=#45F731;X-Ray Visor (?)&pop;"),
])
def test_create_hints_guardians(empty_patches, pickup_index_and_guardian, pickup, item):
    # Setup
    asset_id = 1000
    pickup_index, guardian = pickup_index_and_guardian

    logbook_node, _, world_list = _create_world_list(asset_id, pickup_index)

    patches = dataclasses.replace(
        empty_patches,
        pickup_assignment={
            pickup_index: PickupTarget(pickup, 0),
        },
        hints={
            logbook_node.resource(): Hint(HintType.GUARDIAN,
                                          PrecisionPair(PrecisionPair.detailed(), item[0]),
                                          pickup_index)
        })
    rng = MagicMock()

    # Run
    result = item_hints.create_hints(patches, world_list, rng)

    # Assert
    message = f"{guardian} is guarding {item[1]}."
    assert result == [{'asset_id': asset_id, 'strings': [message, '', message]}]

@pytest.mark.parametrize("item", [
    (HintItemPrecision.DETAILED, "the &push;&main-color=#FF6705B3;Pickup&pop;"),
    (HintItemPrecision.PRECISE_CATEGORY, "a &push;&main-color=#FF6705B3;movement system&pop;"),
    (HintItemPrecision.GENERAL_CATEGORY, "a &push;&main-color=#FF6705B3;major upgrade&pop;"),
    (HintItemPrecision.WRONG_GAME, "the &push;&main-color=#45F731;X-Ray Visor (?)&pop;"),
])
@pytest.mark.parametrize("location", [
    HintLocationPrecision.DETAILED,
    HintLocationPrecision.WORLD_ONLY,
    HintLocationPrecision.WRONG_GAME,
])
def test_create_hints_light_suit_location(empty_patches, pickup, item, location):
    # Setup
    asset_id = 1000
    pickup_index = PickupIndex(50)

    logbook_node, _, world_list = _create_world_list(asset_id, pickup_index)

    patches = dataclasses.replace(
        empty_patches,
        pickup_assignment={
            pickup_index: PickupTarget(pickup, 0),
        },
        hints={
            logbook_node.resource(): Hint(HintType.LIGHT_SUIT_LOCATION,
                                          PrecisionPair(location, item[0]),
                                          pickup_index)
        })
    rng = MagicMock()

    # Run
    result = item_hints.create_hints(patches, world_list, rng)

    # Assert
    if location is HintLocationPrecision.WRONG_GAME and item[0] is HintItemPrecision.WRONG_GAME:
        message = "&push;&main-color=#45F731;Warning! Dark Aether's atmosphere is dangerous!" \
                  " Energized Safe Zones don't last forever!&pop;"
    else:
        message = f"U-Mos's reward for returning the Sanctuary energy is {item[1]}."
    assert result == [{'asset_id': asset_id, 'strings': [message, '', message]}]