from unittest.mock import MagicMock

import pytest

import randovania.generator.filler.player_state
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.generator.filler.filler_configuration import FillerConfiguration
from randovania.layout.base.available_locations import RandomizationMode
from randovania.layout.base.logical_resource_action import LayoutLogicalResourceAction


@pytest.mark.parametrize("major_mode", [RandomizationMode.FULL, RandomizationMode.MAJOR_MINOR_SPLIT])
@pytest.mark.parametrize("has_exclusion", [False, True])
def test_build_available_indices(major_mode: RandomizationMode, has_exclusion: bool):
    # Setup
    world_a = MagicMock()
    world_a.pickup_indices = [PickupIndex(1), PickupIndex(2)]
    world_a.major_pickup_indices = [PickupIndex(1)]

    world_b = MagicMock()
    world_b.pickup_indices = [PickupIndex(3), PickupIndex(4)]
    world_b.major_pickup_indices = [PickupIndex(3)]

    world_list = MagicMock()
    world_list.worlds = [world_a, world_b]

    if has_exclusion:
        exclusion = frozenset([PickupIndex(3)])
    else:
        exclusion = frozenset()
    configuration = FillerConfiguration(major_mode, 0, 0, exclusion, False, LayoutLogicalResourceAction.RANDOMLY)

    # Run
    indices_per_world, all_indices = randovania.generator.filler.player_state.build_available_indices(world_list,
                                                                                                      configuration)

    # Assert
    if major_mode == RandomizationMode.FULL:
        a_pickups = {PickupIndex(1), PickupIndex(2)}
        b_pickups = {PickupIndex(3), PickupIndex(4)}
    else:
        a_pickups = {PickupIndex(1)}
        b_pickups = {PickupIndex(3)}

    if has_exclusion:
        b_pickups.remove(PickupIndex(3))

    assert indices_per_world == [a_pickups, b_pickups]
    assert all_indices == a_pickups | b_pickups
