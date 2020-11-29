import pytest
from PySide2 import QtWidgets
from mock import MagicMock, AsyncMock

from randovania.games.game import RandovaniaGame
from randovania.gui.generate_seed_tab import GenerateSeedTab
from randovania.gui.generated.main_window_ui import Ui_MainWindow


@pytest.fixture(name="tab")
def _tab(skip_qtbot):
    class Window(QtWidgets.QMainWindow, Ui_MainWindow):
        pass

    window = Window()
    window.setupUi(window)

    return GenerateSeedTab(window, MagicMock(), MagicMock())


def test_add_new_preset(tab, preset_manager):
    tab.setup_ui()
    tab._window_manager.preset_manager.add_new_preset.return_value = True

    # Run
    tab._add_new_preset(preset_manager.default_preset)

    # Assert
    tab._window_manager.preset_manager.add_new_preset.assert_called_once_with(preset_manager.default_preset)
    assert not tab._action_delete.isEnabled()


@pytest.mark.parametrize("has_existing_window", [False, True])
@pytest.mark.asyncio
async def test_on_customize_button(tab, mocker, has_existing_window):
    mock_settings_window = mocker.patch("randovania.gui.generate_seed_tab.LogicSettingsWindow")
    mock_execute_dialog = mocker.patch("randovania.gui.lib.async_dialog.execute_dialog", new_callable=AsyncMock)
    mock_execute_dialog.return_value = QtWidgets.QDialog.Accepted
    tab._add_new_preset = MagicMock()
    tab._logic_settings_window = MagicMock() if has_existing_window else None

    # Run
    await tab._on_customize_button()

    # Assert
    if has_existing_window:
        tab._logic_settings_window.raise_.assert_called_once_with()
        mock_settings_window.assert_not_called()
        mock_execute_dialog.assert_not_awaited()
        tab._add_new_preset.assert_not_called()
    else:
        mock_settings_window.assert_called_once()
        mock_execute_dialog.assert_awaited_once_with(mock_settings_window.return_value)
        tab._add_new_preset.assert_called_once()


@pytest.mark.parametrize("game", [RandovaniaGame.PRIME2, RandovaniaGame.PRIME3])
def test_on_options_changed_select_preset(tab, preset_manager, game):
    preset = preset_manager.default_preset_for_game(game)

    tab._window_manager.preset_manager = preset_manager
    tab.setup_ui()

    tab._options.selected_preset_name = preset.name

    # Run
    tab.on_options_changed(tab._options)

    # Assert
    assert tab._current_preset_data == preset


def test_select_game(tab, preset_manager):
    tab._window_manager.preset_manager = preset_manager
    tab.setup_ui()

    tab.select_game(RandovaniaGame.PRIME3)
    assert tab._current_preset_data.game == RandovaniaGame.PRIME3

    tab.select_game(RandovaniaGame.PRIME2)
    assert tab._current_preset_data.game == RandovaniaGame.PRIME2
