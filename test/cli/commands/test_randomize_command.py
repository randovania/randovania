import pytest
from mock import MagicMock, ANY, AsyncMock

from randovania.cli.commands import randomize_command
from randovania.games.game import RandovaniaGame
from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches
from randovania.interface_common.options import Options
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.layout.prime1.prime_cosmetic_patches import PrimeCosmeticPatches
from randovania.layout.prime2.echoes_cosmetic_patches import EchoesCosmeticPatches


@pytest.mark.parametrize(["game", "cosmetic_class"], [
    (RandovaniaGame.METROID_PRIME, PrimeCosmeticPatches),
    (RandovaniaGame.METROID_PRIME_ECHOES, EchoesCosmeticPatches),
])
@pytest.mark.parametrize("with_permalink", [False, True])
def test_randomize_command_logic(mocker, with_permalink, game, cosmetic_class):
    mock_from_str = mocker.patch("randovania.layout.permalink.Permalink.from_str")
    mock_from_file = mocker.patch("randovania.layout.layout_description.LayoutDescription.from_file")
    mock_generate: AsyncMock = mocker.patch("randovania.generator.generator.generate_and_validate_description",
                                            new_callable=AsyncMock)

    mock_provider_for: MagicMock = mocker.patch("randovania.games.patcher_provider.PatcherProvider.patcher_for_game")
    patcher: MagicMock = mock_provider_for.return_value

    args = MagicMock()
    if with_permalink:
        layout_description = mock_generate.return_value
    else:
        layout_description = mock_from_file.return_value
        args.permalink = None

    preset = MagicMock()
    preset.game = game
    layout_description.permalink.player_count = 4
    layout_description.permalink.get_preset = MagicMock(return_value=preset)

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
    randomize_command.randomize_command_logic(args)

    # Assert
    mock_provider_for.assert_called_once_with(preset.game)

    patcher.create_patch_data.assert_called_once_with(layout_description, players_config, cosmetic_class())
    patcher.patch_game.assert_called_once_with(args.input_file, args.output_file,
                                               patcher.create_patch_data.return_value,
                                               Options.with_default_data_dir().internal_copies_path,
                                               ANY)

    if with_permalink:
        mock_from_str.assert_called_once_with(args.permalink)
        mock_generate.assert_awaited_once_with(permalink=mock_from_str.return_value,
                                               status_update=ANY,
                                               validate_after_generation=True)
        mock_from_file.assert_not_called()
    else:
        mock_from_str.assert_not_called()
        mock_generate.assert_not_called()
        mock_from_file.assert_called_once_with(args.log_file)
