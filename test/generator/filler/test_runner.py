from random import Random
from unittest.mock import MagicMock, patch

import pytest

from randovania.game_description.game_patches import GamePatches
from randovania.game_description.hint import Hint, HintType
from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.node import LogbookNode
from randovania.game_description.resources.pickup_entry import PickupEntry, ConditionalResources
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.generator.filler import runner
from randovania.layout.layout_configuration import LayoutConfiguration


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


@patch("randovania.generator.filler.runner.retcon_playthrough_filler", autospec=True)
def test_run_filler(mock_retcon_playthrough_filler: MagicMock,
                    echoes_game_description,
                    pickup
                    ):
    # Setup
    configuration = LayoutConfiguration.default()
    rng = Random(5000)
    status_update = MagicMock()
    item_pool = [pickup]
    patches = GamePatches.with_game(echoes_game_description)

    logbook_nodes = [node for node in echoes_game_description.world_list.all_nodes if isinstance(node, LogbookNode)]

    mock_retcon_playthrough_filler.return_value = patches.assign_hint(
        logbook_nodes[0].resource(), Hint(HintType.LOCATION, None, PickupIndex(0))
    ).assign_pickup_assignment({PickupIndex(1): pickup})

    # Run
    result_patches, remaining_items = runner.run_filler(configuration, echoes_game_description,
                                                        item_pool, patches,
                                                        rng, status_update)

    # Assert
    assert len(result_patches.hints) == len(logbook_nodes)
    assert [hint for hint in patches.hints.values()
            if hint.item_precision is None or hint.location_precision is None] == []
    assert remaining_items == [pickup]
