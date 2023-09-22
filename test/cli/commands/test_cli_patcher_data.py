from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

from randovania.cli.commands import patcher_data
from randovania.interface_common.players_configuration import PlayersConfiguration

if TYPE_CHECKING:
    import pytest_mock


async def test_patcher_data_logic_async(mocker: pytest_mock.MockerFixture):
    mock_from_file = mocker.patch("randovania.layout.layout_description.LayoutDescription.from_file")
    mock_json = mocker.patch("json.dumps", autospec=True)

    args = MagicMock()
    layout_description = mock_from_file.return_value

    preset = MagicMock()
    layout_description.world_count = 4
    layout_description.get_preset = MagicMock(return_value=preset)

    players_config = PlayersConfiguration(
        args.player_index,
        {
            0: "Player 1",
            1: "Player 2",
            2: "Player 3",
            3: "Player 4",
        },
    )
    cosmetic_patches = preset.game.data.layout.cosmetic_patches.default.return_value

    # Run
    await patcher_data.patcher_data_command_logic_async(args)

    # Assert
    preset.game.data.layout.cosmetic_patches.default.assert_called_once_with()
    preset.game.patch_data_factory.assert_called_once_with(layout_description, players_config, cosmetic_patches)
    mock_json.assert_called_once_with(
        preset.game.patch_data_factory.return_value.create_data.return_value,
        indent=4,
    )


def test_patcher_data_logic(mocker: pytest_mock.MockerFixture):
    args = MagicMock()
    mock_run = mocker.patch("asyncio.run")
    mock_async = mocker.patch(
        "randovania.cli.commands.patcher_data.patcher_data_command_logic_async", new_callable=MagicMock
    )

    # Run
    patcher_data.patcher_data_command_logic(args)

    # Assert
    mock_async.assert_called_once_with(args)
    mock_run.assert_called_once_with(mock_async.return_value)
