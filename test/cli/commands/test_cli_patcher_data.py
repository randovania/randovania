from unittest.mock import MagicMock

from randovania.cli.commands import patcher_data
from randovania.interface_common.players_configuration import PlayersConfiguration


def test_patcher_data_logic(mocker):
    mock_from_file: MagicMock = mocker.patch("randovania.layout.layout_description.LayoutDescription.from_file")
    mock_json = mocker.patch("json.dumps", autospec=True)

    args = MagicMock()
    layout_description = mock_from_file.return_value

    preset = MagicMock()
    layout_description.player_count = 4
    layout_description.get_preset = MagicMock(return_value=preset)

    players_config = PlayersConfiguration(
        args.player_index,
        {
            0: "Player 1",
            1: "Player 2",
            2: "Player 3",
            3: "Player 4",
        }
    )
    cosmetic_patches = preset.game.data.layout.cosmetic_patches.default.return_value

    # Run
    patcher_data.patcher_data_command_logic(args)

    # Assert
    preset.game.data.layout.cosmetic_patches.default.assert_called_once_with()
    preset.game.patch_data_factory.assert_called_once_with(layout_description, players_config, cosmetic_patches)
    mock_json.assert_called_once_with(
        preset.game.patch_data_factory.return_value.create_data.return_value,
        indent=4,
    )
