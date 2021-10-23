from typing import Callable, Union

import pytest
from mock import MagicMock, patch, call, AsyncMock

import randovania
from randovania.generator import generator
from randovania.generator.filler.runner import FillerPlayerResult
from randovania.layout.layout_description import LayoutDescription
from randovania.resolver.exceptions import InvalidConfiguration


@patch("randovania.generator.generator._validate_item_pool_size", autospec=True)
@patch("randovania.generator.generator.create_player_pool", autospec=True)
@patch("randovania.generator.generator._distribute_remaining_items", autospec=True)
@patch("randovania.generator.generator.Random", autospec=False)
@pytest.mark.asyncio
async def test_create_patches(mock_random: MagicMock,
                              mock_distribute_remaining_items: MagicMock,
                              mock_create_player_pool: MagicMock,
                              mock_validate_item_pool_size: MagicMock,
                              mocker,
                              ):
    # Setup
    filler_result = MagicMock()
    mock_run_filler: AsyncMock = mocker.patch("randovania.generator.generator.run_filler", new_callable=AsyncMock,
                                              return_value=filler_result)

    num_players = 1
    rng = mock_random.return_value
    status_update: Union[MagicMock, Callable[[str], None]] = MagicMock()
    player_pools = [MagicMock() for _ in range(num_players)]
    presets = [MagicMock() for _ in range(num_players)]

    mock_create_player_pool.side_effect = player_pools

    permalink = MagicMock()
    permalink.get_preset.side_effect = lambda i: presets[i]

    # Run
    result = await generator._create_description(permalink, status_update, 0)

    # Assert
    mock_random.assert_called_once_with(permalink.as_bytes)
    mock_create_player_pool.assert_has_calls([
        call(rng, presets[i].configuration, i, num_players)
        for i in range(num_players)
    ])
    mock_validate_item_pool_size.assert_has_calls([
        call(player_pools[i].pickups, player_pools[i].game, player_pools[i].configuration)
        for i in range(num_players)
    ])
    mock_run_filler.assert_awaited_once_with(rng, {i: player_pools[i] for i in range(num_players)}, status_update)
    mock_distribute_remaining_items.assert_called_once_with(rng, filler_result.player_results)

    assert result == LayoutDescription(
        permalink=permalink,
        version=randovania.VERSION,
        all_patches=mock_distribute_remaining_items.return_value,
        item_order=filler_result.action_log,
    )


def test_distribute_remaining_items_no_locations_left(echoes_game_description):
    # Setup
    rng = MagicMock()
    player_result = FillerPlayerResult(
        game=echoes_game_description,
        patches=echoes_game_description.create_game_patches(),
        unassigned_pickups=[MagicMock()] * 1000,
    )
    filler_results = {0: player_result}

    # Run
    with pytest.raises(InvalidConfiguration,
                       match=r"Received 1000 remaining pickups, but there's only \d+ unassigned locations."):
        generator._distribute_remaining_items(rng, filler_results)
