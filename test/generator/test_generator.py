from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest

from randovania.game_description.pickup.pickup_entry import PickupEntry, PickupModel
from randovania.game_description.requirements.base import Requirement
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.generator import generator
from randovania.generator.filler.filler_configuration import FillerPlayerResult, FillerResults
from randovania.layout.base.logical_pickup_placement_configuration import LogicalPickupPlacementConfiguration
from randovania.layout.exceptions import InvalidConfiguration
from randovania.layout.layout_description import LayoutDescription

if TYPE_CHECKING:
    from collections.abc import Callable


@patch("randovania.generator.generator._validate_pickup_pool_size", autospec=True)
@patch("randovania.generator.generator.create_player_pool", autospec=True)
@patch("randovania.generator.generator._distribute_remaining_items", autospec=True)
async def test_create_patches(
    mock_distribute_remaining_items: MagicMock,
    mock_create_player_pool: MagicMock,
    mock_validate_item_pool_size: MagicMock,
    mocker,
):
    # Setup
    filler_result = MagicMock()
    mock_run_filler: AsyncMock = mocker.patch(
        "randovania.generator.generator.run_filler", new_callable=AsyncMock, return_value=filler_result
    )
    mock_dock_weakness_distributor: AsyncMock = mocker.patch(
        "randovania.generator.dock_weakness_distributor.distribute_post_fill_weaknesses",
        new_callable=AsyncMock,
        return_value=filler_result,
    )
    mock_specific_location_hints: AsyncMock = mocker.patch(
        "randovania.generator.hint_distributor.distribute_specific_location_hints",
        new_callable=AsyncMock,
        return_value=filler_result,
    )
    mock_distribute_remaining_items.return_value = filler_result

    generator_parameters = MagicMock()
    generator_parameters.get_preset.side_effect = lambda i: presets[i]

    num_players = 1
    rng = generator_parameters.create_rng.return_value
    status_update: MagicMock | Callable[[str], None] = MagicMock()
    player_pools = [MagicMock() for _ in range(num_players)]
    presets: list = [MagicMock() for _ in range(num_players)]
    world_names = [f"Test {i + 1}" for i in range(num_players)]

    mock_create_player_pool.side_effect = player_pools

    # Run
    result = await generator._create_description(generator_parameters, status_update, 0, world_names)

    # Assert
    generator_parameters.create_rng.assert_called_once_with()
    mock_create_player_pool.assert_has_calls(
        [call(rng, presets[i].configuration, i, num_players, world_names[i], status_update) for i in range(num_players)]
    )
    mock_validate_item_pool_size.assert_has_calls(
        [call(player_pools[i].pickups, player_pools[i].game, player_pools[i].configuration) for i in range(num_players)]
    )
    mock_run_filler.assert_awaited_once_with(
        rng, [player_pools[i] for i in range(num_players)], world_names, status_update
    )
    mock_distribute_remaining_items.assert_called_once_with(rng, filler_result, presets)
    mock_dock_weakness_distributor.assert_called_once_with(rng, filler_result, status_update)
    mock_specific_location_hints.assert_called_once_with(rng, filler_result, player_pools)

    assert result == LayoutDescription.create_new(
        generator_parameters=generator_parameters,
        all_patches={},
        item_order=filler_result.action_log,
    )


def test_distribute_remaining_items_no_locations_left(
    echoes_game_description, echoes_game_patches, default_echoes_preset
):
    # Setup
    rng = MagicMock()
    player_result = FillerPlayerResult(
        game=echoes_game_description,
        patches=echoes_game_patches,
        unassigned_pickups=[MagicMock()] * 1000,
    )
    filler_results = FillerResults({0: player_result}, ())

    # Run
    with pytest.raises(
        InvalidConfiguration, match=r"Received 881 remaining pickups, but there's only \d+ unassigned locations."
    ):
        generator._distribute_remaining_items(rng, filler_results, [default_echoes_preset])


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
        generator.victory_condition_for_pickup_placement(pickups, blank_game_description, placement_config)
    )

    # Assert
    # print(victory_str)
    assert victory_str == expected
