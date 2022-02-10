import pytest
from mock import MagicMock, ANY, AsyncMock

from randovania.cli.commands import apply_layout
from randovania.games.game import RandovaniaGame
from randovania.games.prime1.layout.prime_cosmetic_patches import PrimeCosmeticPatches
from randovania.games.prime2.layout.echoes_cosmetic_patches import EchoesCosmeticPatches
from randovania.interface_common.options import Options
from randovania.interface_common.players_configuration import PlayersConfiguration


@pytest.mark.parametrize(["game", "cosmetic_class"], [
    (RandovaniaGame.METROID_PRIME, PrimeCosmeticPatches),
    (RandovaniaGame.METROID_PRIME_ECHOES, EchoesCosmeticPatches),
])
def test_apply_layout_logic(mocker, game, cosmetic_class):
    mock_from_file: MagicMock = mocker.patch("randovania.layout.layout_description.LayoutDescription.from_file")
    mock_provider_for: MagicMock = mocker.patch("randovania.patching.patcher_provider.PatcherProvider.patcher_for_game")
    patcher: MagicMock = mock_provider_for.return_value

    args = MagicMock()
    layout_description = mock_from_file.return_value

    preset = MagicMock()
    preset.game = game
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

    # Run
    apply_layout.randomize_command_logic(args)

    # Assert
    mock_provider_for.assert_called_once_with(preset.game)

    patcher.create_patch_data.assert_called_once_with(layout_description, players_config, cosmetic_class())
    patcher.patch_game.assert_called_once_with(args.input_file, args.output_file,
                                               patcher.create_patch_data.return_value,
                                               Options.with_default_data_dir().internal_copies_path,
                                               ANY)
    mock_from_file.assert_called_once_with(args.log_file)
