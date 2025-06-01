from __future__ import annotations

from random import Random

import pytest

from randovania.game_description import default_database
from randovania.game_description.pickup.pickup_entry import PickupEntry, PickupModel
from randovania.game_description.requirements.base import Requirement
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.layout.base.logical_pickup_placement_configuration import LogicalPickupPlacementConfiguration
from randovania.resolver import bootstrap


def test_logic_bootstrap(preset_manager, game_enum):
    configuration = preset_manager.default_preset_for_game(game_enum).get_preset().configuration
    game = default_database.game_description_for(configuration.game)

    patches = game_enum.generator.base_patches_factory.create_base_patches(configuration, Random(1000), game, False, 0)

    new_game, state = game_enum.generator.bootstrap.logic_bootstrap(
        configuration,
        game.get_mutable(),
        patches,
    )

    for misc_resource in game.resource_database.misc:
        assert state.resources.is_resource_set(misc_resource)

    assert state.node.identifier == configuration.starting_location.locations[0]


@pytest.mark.parametrize(
    "logical_placement_cases",
    [
        (
            LogicalPickupPlacementConfiguration.MINIMAL,
            "Trivial",
        ),
        (
            LogicalPickupPlacementConfiguration.MAJORS,
            "Major ≥ 1",
        ),
        (
            LogicalPickupPlacementConfiguration.ALL,
            "(Major ≥ 1 and Minor ≥ 1)",
        ),
    ],
)
def test_victory_condition_for_pickup_placement(
    mocker,
    blank_game_description,
    blank_pickup_database,
    default_generator_params,
    default_generator_params_minor,
    logical_placement_cases,
):
    # Setup
    placement_config, expected = logical_placement_cases
    mocker.patch.object(blank_game_description, "victory_condition", Requirement.trivial())

    pickups = [
        PickupEntry(
            name="Major Item",
            model=PickupModel(
                game=blank_game_description.game,
                name="EnergyTransferModule",
            ),
            gui_category=blank_pickup_database.pickup_categories["gear"],
            hint_features=frozenset((blank_pickup_database.pickup_categories["gear"],)),
            progression=(
                (
                    ItemResourceInfo(
                        resource_index=2,
                        long_name="Major",
                        short_name="major",
                        max_capacity=1,
                    ),
                    1,
                ),
            ),
            generator_params=default_generator_params,
            resource_lock=None,
            unlocks_resource=False,
        ),
        PickupEntry(
            name="Minor Item",
            model=PickupModel(
                game=blank_game_description.game,
                name="EnergyTransferModule",
            ),
            gui_category=blank_pickup_database.pickup_categories["ammo"],
            hint_features=frozenset((blank_pickup_database.pickup_categories["ammo"],)),
            progression=(
                (
                    ItemResourceInfo(
                        resource_index=3,
                        long_name="Minor",
                        short_name="minor",
                        max_capacity=1,
                    ),
                    1,
                ),
            ),
            generator_params=default_generator_params_minor,
            resource_lock=None,
            unlocks_resource=False,
        ),
    ]

    # Run
    victory_str = str(
        bootstrap.victory_condition_for_pickup_placement(pickups, blank_game_description, placement_config)
    )

    # Assert
    # print(victory_str)
    assert victory_str == expected
