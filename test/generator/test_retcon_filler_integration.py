from __future__ import annotations

import dataclasses
from unittest.mock import MagicMock

import pytest

import randovania.generator.filler.player_state
from randovania.game_description.db.region_list import RegionList
from randovania.game_description.resources.pickup_index import PickupIndex


@pytest.mark.parametrize("has_exclusion", [False, True])
def test_build_available_indices(has_exclusion: bool, default_filler_config):
    # Setup
    world_a = MagicMock()
    world_a.pickup_indices = [PickupIndex(1), PickupIndex(2)]
    world_a.major_pickup_indices = [PickupIndex(1)]

    world_b = MagicMock()
    world_b.pickup_indices = [PickupIndex(3), PickupIndex(4)]
    world_b.major_pickup_indices = [PickupIndex(3)]

    region_list = MagicMock(spec=RegionList)
    region_list.regions = [world_a, world_b]

    if has_exclusion:
        exclusion = frozenset([PickupIndex(3)])
    else:
        exclusion = frozenset()
    configuration = dataclasses.replace(default_filler_config, indices_to_exclude=exclusion)

    # Run
    indices_per_world, all_indices = randovania.generator.filler.player_state.build_available_indices(
        region_list, configuration
    )

    # Assert
    a_pickups = {PickupIndex(1), PickupIndex(2)}
    b_pickups = {PickupIndex(3), PickupIndex(4)}

    if has_exclusion:
        b_pickups.remove(PickupIndex(3))

    assert indices_per_world == [a_pickups, b_pickups]
    assert all_indices == a_pickups | b_pickups
