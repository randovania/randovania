from unittest.mock import MagicMock, ANY

import pytest

from randovania.cli.commands import randomize_command
from randovania.interface_common.cosmetic_patches import CosmeticPatches
from randovania.interface_common.players_configuration import PlayersConfiguration


@pytest.mark.parametrize("with_permalink", [False, True])
def test_randomize_command_logic(mocker, with_permalink):
    mock_from_str = mocker.patch("randovania.layout.permalink.Permalink.from_str")
    mock_from_file = mocker.patch("randovania.layout.layout_description.LayoutDescription.from_file")
    mock_generate = mocker.patch("randovania.generator.generator.generate_description")
    mock_apply = mocker.patch("randovania.games.prime.claris_randomizer.apply_layout")

    args = MagicMock()
    if with_permalink:
        layout_description = mock_generate.return_value
    else:
        layout_description = mock_from_file.return_value
        args.permalink = None

    cosmetic_patches = CosmeticPatches(
        disable_hud_popup=args.disable_hud_popup,
        speed_up_credits=args.speed_up_credits)

    # Run
    randomize_command.randomize_command_logic(args)

    # Assert
    mock_apply.assert_called_once_with(
        description=layout_description,
        cosmetic_patches=cosmetic_patches,
        backup_files_path=args.backup_files,
        progress_update=ANY,
        game_root=args.game_files,
        players_config=PlayersConfiguration(0, {0: "You"})
    )

    if with_permalink:
        mock_from_str.assert_called_once_with(args.permalink)
        mock_generate.assert_called_once_with(permalink=mock_from_str.return_value,
                                              status_update=ANY,
                                              validate_after_generation=True)
        mock_from_file.assert_not_called()
    else:
        mock_from_str.assert_not_called()
        mock_generate.assert_not_called()
        mock_from_file.assert_called_once_with(args.log_file)
