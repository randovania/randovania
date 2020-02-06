from typing import Callable, Union
from unittest.mock import MagicMock, patch

from randovania.game_description.default_database import default_prime2_game_description
from randovania.generator import generator


@patch("randovania.generator.generator._assign_remaining_items", autospec=True)
@patch("randovania.generator.generator.run_filler", autospec=True)
@patch("randovania.generator.generator._validate_item_pool_size", autospec=True)
@patch("randovania.generator.base_patches_factory.create_base_patches", autospec=True)
@patch("randovania.generator.item_pool.pool_creator.calculate_item_pool", autospec=True)
@patch("randovania.generator.generator.Random", autospec=False)  # TODO: pytest-qt bug
def test_create_patches(mock_random: MagicMock,
                        mock_calculate_item_pool: MagicMock,
                        mock_create_base_patches: MagicMock,
                        mock_validate_item_pool_size: MagicMock,
                        mock_run_filler: MagicMock,
                        mock_assign_remaining_items: MagicMock,
                        ):
    # Setup
    game = default_prime2_game_description()
    status_update: Union[MagicMock, Callable[[str], None]] = MagicMock()

    permalink = MagicMock()
    pool_patches = MagicMock()
    item_pool = MagicMock()
    filler_patches = MagicMock()
    remaining_items = MagicMock()

    mock_calculate_item_pool.return_value = pool_patches, item_pool
    mock_run_filler.return_value = filler_patches, remaining_items

    # Run
    result = generator._create_randomized_patches(permalink, game, status_update)

    # Assert
    mock_random.assert_called_once_with(permalink.as_str)
    mock_create_base_patches.assert_called_once_with(permalink.layout_configuration, mock_random.return_value, game)

    # pool
    mock_calculate_item_pool.assert_called_once_with(permalink.layout_configuration,
                                                     game.resource_database,
                                                     mock_create_base_patches.return_value)

    mock_validate_item_pool_size.assert_called_once_with(item_pool, game)
    mock_run_filler.assert_called_once_with(
        permalink.layout_configuration, game, item_pool, pool_patches, mock_random.return_value, status_update
    )
    mock_assign_remaining_items.assert_called_once_with(
        mock_random.return_value, game.world_list, filler_patches.pickup_assignment,
        remaining_items, permalink.layout_configuration.randomization_mode
    )
    filler_patches.assign_pickup_assignment.assert_called_once_with(mock_assign_remaining_items.return_value)

    assert result == filler_patches.assign_pickup_assignment.return_value
