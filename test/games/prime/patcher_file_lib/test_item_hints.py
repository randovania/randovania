import dataclasses
from unittest.mock import MagicMock

import pytest

from randovania.game_description.area import Area
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
    pickup_node = PickupNode("Pickup Node", True, 1, pickup_index)

    world_list = WorldList([
        World("World", 5000, [
            Area("Area", 10000, 0, [logbook_node, pickup_node], {}),
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
    message = ("An &push;&main-color=#a84343;Energy Transfer Module&pop; can be found at "
               "&push;&main-color=#a84343;World - Area&pop;.")
    assert result == [
        {'asset_id': asset_id, 'strings': [message, '', message]}
    ]


@pytest.mark.parametrize("item", [
    (HintItemPrecision.DETAILED, "The &push;&main-color=#a84343;Pickup&pop;"),
    (HintItemPrecision.PRECISE_CATEGORY, "A &push;&main-color=#a84343;movement system&pop;"),
    (HintItemPrecision.GENERAL_CATEGORY, "A &push;&main-color=#a84343;major item&pop;"),
    (HintItemPrecision.WRONG_GAME, "The &push;&main-color=#45f731;X-Ray Visor (?)&pop;"),
])
@pytest.mark.parametrize("location", [
    (HintLocationPrecision.DETAILED, "&push;&main-color=#a84343;World - Area&pop;"),
    (HintLocationPrecision.WORLD_ONLY, "&push;&main-color=#a84343;World&pop;"),
    (HintLocationPrecision.WRONG_GAME, "&push;&main-color=#45f731;Tower (?)&pop;"),
])
def test_create_hints_item_detailed(empty_patches, pickup,
                                    item, location):
    # Setup
    asset_id = 1000
    pickup_index = PickupIndex(50)

    logbook_node, _, world_list = _create_world_list(asset_id, pickup_index)

    patches = dataclasses.replace(
        empty_patches,
        pickup_assignment={
            pickup_index: pickup,
        },
        hints={
            logbook_node.resource(): Hint(HintType.LOCATION,
                                          PrecisionPair(location[0], item[0]),
                                          pickup_index)
        })
    rng = MagicMock()
    rng.choice.side_effect = lambda x: x[0]

    # Run
    result = item_hints.create_hints(patches, world_list, rng)

    # Assert
    if location[0] == HintLocationPrecision.WRONG_GAME and item[0] == HintItemPrecision.WRONG_GAME:
        message = "&push;&main-color=#45f731;Did you remember to check Trial Tunnel?&pop;"
    else:
        message = "{0} can be found at {1}.".format(item[1], location[1])
    assert result == [
        {'asset_id': asset_id, 'strings': [message, '', message]}
    ]
