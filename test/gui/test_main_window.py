from pathlib import Path
from typing import Union
from unittest.mock import MagicMock, patch

import pytest

from randovania.gui.main_window import MainWindow
from randovania.interface_common.options import Options

pytestmark = pytest.mark.skipif(
    pytest.config.option.skip_gui_tests,
    reason="skipped due to --skip-gui-tests")


def create_window(options: Union[Options, MagicMock]) -> MainWindow:
    return MainWindow(options, False)


@pytest.fixture(name="default_main_window")
def _default_main_window() -> MainWindow:
    return create_window(Options(MagicMock()))


@patch("randovania.gui.iso_management_window.ISOManagementWindow.load_game", autospec=True)
def test_drop_iso_event(mock_load_game: MagicMock,
                        default_main_window: MainWindow,
                        qtbot,
                        ):
    # Setup
    event = MagicMock()
    urls = [MagicMock(), MagicMock()]
    urls[0].toLocalFile.return_value = "directory/games/seed.json"
    urls[1].toLocalFile.return_value = "directory/games/game.iso"
    event.mimeData.return_value.urls.return_value = urls

    # Run
    default_main_window.dropEvent(event)

    # Assert
    mock_load_game.assert_called_once_with(default_main_window.windows[0], Path("directory/games/game.iso"))


@patch("randovania.gui.iso_management_window.ISOManagementWindow.load_game", autospec=True)
def test_drop_random_event(mock_load_game: MagicMock,
                           default_main_window: MainWindow,
                           qtbot,
                           ):
    # Setup
    event = MagicMock()
    urls = [MagicMock(), MagicMock()]
    urls[0].toLocalFile.return_value = "directory/games/seed.json"
    urls[1].toLocalFile.return_value = "directory/games/game.png"
    event.mimeData.return_value.urls.return_value = []

    # Run
    default_main_window.dropEvent(event)

    # Assert
    mock_load_game.assert_not_called()
