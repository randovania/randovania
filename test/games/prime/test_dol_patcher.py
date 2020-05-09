from pathlib import Path
from unittest.mock import patch, MagicMock, ANY

from randovania.games.prime import dol_patcher
from randovania.interface_common.echoes_user_preferences import EchoesUserPreferences


@patch("randovania.games.prime.dol_patcher._apply_game_options_patch", autospec=True)
@patch("randovania.games.prime.dol_patcher._apply_string_display_patch", autospec=True)
@patch("randovania.games.prime.dol_patcher._get_dol_path", autospec=True)
@patch("randovania.games.prime.dol_patcher._read_binary_version", autospec=True)
def test_apply_patches(mock_read_binary_version: MagicMock,
                       mock_get_dol_path: MagicMock,
                       mock_apply_string_display_patch: MagicMock,
                       mock_apply_game_options_patch: MagicMock,
                       ):
    # Setup
    game_root = MagicMock()
    cosmetic_patches = MagicMock()
    mock_read_binary_version.return_value = dol_patcher._GC_NTSC_DOL_VERSION
    version_patches = dol_patcher._ALL_VERSIONS_PATCHES[dol_patcher._GC_NTSC_DOL_VERSION]
    dol_file = mock_get_dol_path.return_value.open.return_value.__enter__.return_value

    # Run
    dol_patcher.apply_patches(game_root, cosmetic_patches)

    # Assert
    mock_read_binary_version.assert_called_once_with(game_root)
    mock_get_dol_path.assert_called_once_with(game_root)
    mock_apply_string_display_patch.assert_called_once_with(version_patches.string_display, dol_file)
    mock_apply_game_options_patch.assert_called_once_with(
        version_patches.game_options_file_offset,
        cosmetic_patches.user_preferences, dol_file
    )


def test_get_dol_path():
    assert dol_patcher._get_dol_path(Path("foo")) == Path("foo", "sys", "main.dol")


def test_read_binary_version(tmpdir):
    tmpdir.join("sys").mkdir()
    tmpdir.join("sys", "main.dol").write_binary(b"123456789012345678901234567\x00\x3A\x22\xA0")
    assert dol_patcher._read_binary_version(Path(tmpdir)) == dol_patcher._GC_NTSC_DOL_VERSION


def test_apply_string_display_patch():
    offsets = dol_patcher.StringDisplayPatchOffsets(0x15, 0, 0, 0)
    dol_file = MagicMock()

    # Run
    dol_patcher._apply_string_display_patch(offsets, dol_file)

    # Assert
    dol_file.seek.assert_called_once_with(0x15)
    dol_file.write.assert_called_once_with(ANY)


def test_apply_game_options_patch():
    offset = 0x15
    dol_file = MagicMock()
    user_preferences = EchoesUserPreferences()

    # Run
    dol_patcher._apply_game_options_patch(offset, user_preferences, dol_file)

    # Assert
    dol_file.seek.assert_called_once_with(0x15)
    dol_file.write.assert_called_once_with(ANY)
