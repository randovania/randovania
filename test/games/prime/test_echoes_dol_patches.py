from unittest.mock import MagicMock, ANY

from randovania.games.prime import echoes_dol_patches
from randovania.interface_common.echoes_user_preferences import EchoesUserPreferences


def test_apply_game_options_patch():
    offset = 0x15
    dol_file = MagicMock()
    user_preferences = EchoesUserPreferences()

    # Run
    echoes_dol_patches.apply_game_options_patch(offset, user_preferences, dol_file)

    # Assert
    dol_file.write.assert_called_once_with(53, ANY)
