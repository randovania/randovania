from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from randovania.game_description.assignment import PickupTarget
from randovania.game_description.db.hint_node import HintNode
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.games.fusion.generator.hint_distributor import FusionHintDistributor


@pytest.mark.parametrize(
    ("target_pickup", "target_player", "features", "expected"),
    [
        ("Charge Beam", 0, {"beam", "charge"}, False),
        ("Gravity Suit", 0, {"suit", "life_support"}, True),
        ("Infant Metroid 1", 0, {"key"}, False),
        ("Energy Tank", 0, {"energy_tank"}, True),
        ("Level 1 Keycard", 0, set(), True),
        ("Level 2 Keycard", 0, set(), False),
        ("Level 2 Keycard", 1, set(), True),
    ],
)
def test_fusion_interesting_pickups(
    target_pickup: str, target_player: int, features: set[str], expected: bool, fusion_game_description
):
    # Setup
    hint_node = fusion_game_description.region_list.typed_node_by_identifier(
        NodeIdentifier.create("Sector 1 (SRX)", "Entrance Navigation Room", "Navigation Terminal"),
        HintNode,
    )
    hint_distributor = FusionHintDistributor()

    target = MagicMock(spec=PickupTarget)
    target.pickup.name = target_pickup
    target.pickup.has_hint_feature = lambda feat: feat in features
    target.player = target_player

    # Run
    result = hint_distributor.is_pickup_interesting(target, 0, hint_node)

    # Assert
    assert result == expected
