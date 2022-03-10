import pytest
from PySide6 import QtWidgets
from mock import MagicMock, AsyncMock

from randovania.games.game import RandovaniaGame, DevelopmentState
from randovania.gui.generate_seed_tab import GenerateSeedTab
from randovania.gui.generated.main_window_ui import Ui_MainWindow
from randovania.interface_common.options import Options
from randovania.layout.generator_parameters import GeneratorParameters
from randovania.layout.permalink import Permalink


@pytest.fixture(name="tab")
def _tab(skip_qtbot):
    class Window(QtWidgets.QMainWindow, Ui_MainWindow):
        pass

    window = Window()
    window.setupUi(window)

    return GenerateSeedTab(window, MagicMock(), MagicMock())


def test_add_new_preset(tab, preset_manager):
    preset = preset_manager.default_preset
    tab.setup_ui()
    tab.window.create_preset_tree.select_preset = MagicMock()

    # Run
    tab._add_new_preset(preset)

    # Assert
    tab._window_manager.preset_manager.add_new_preset.assert_called_once_with(preset)
    tab.window.create_preset_tree.select_preset.assert_called_once_with(preset)


@pytest.mark.parametrize("has_existing_window", [False, True])
async def test_on_customize_button(tab, mocker, has_existing_window):
    mock_settings_window = mocker.patch("randovania.gui.generate_seed_tab.CustomizePresetDialog")
    mock_execute_dialog = mocker.patch("randovania.gui.lib.async_dialog.execute_dialog", new_callable=AsyncMock)
    mock_execute_dialog.return_value = QtWidgets.QDialog.Accepted
    tab._add_new_preset = MagicMock()
    tab._logic_settings_window = MagicMock() if has_existing_window else None
    tab.window.create_preset_tree = MagicMock()
    tab.window.create_preset_tree.selectedItems.return_value = [MagicMock()]

    # Run
    await tab._on_customize_preset()

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


@pytest.mark.parametrize("allow_experimental", [False, True])
def test_on_options_changed_select_preset(tab, preset_manager, game_enum, is_dev_version, allow_experimental):
    preset = preset_manager.default_preset_for_game(game_enum)

    tab._window_manager.preset_manager = preset_manager
    tab.setup_ui()

    tab._options.experimental_games = allow_experimental
    tab._options.selected_preset_uuid = preset.uuid

    dev_state = game_enum.data.development_state
    if dev_state.is_stable or (allow_experimental and (is_dev_version or dev_state == DevelopmentState.EXPERIMENTAL)):
        expected_result = preset
    else:
        expected_result = None

    # Run
    tab.on_options_changed(tab._options)

    # Assert
    assert tab._current_preset_data == expected_result


@pytest.mark.parametrize("allow_experimental", [False, True])
@pytest.mark.parametrize("game", RandovaniaGame)
def test_click_on_preset_tree(tab, preset_manager, game: RandovaniaGame, skip_qtbot, tmp_path, allow_experimental):
    preset = preset_manager.default_preset_for_game(game)

    options = Options(tmp_path, None)
    with options:
        options.experimental_games = allow_experimental
    options.on_options_changed = lambda: tab.on_options_changed(options)

    tab._options = options
    tab._window_manager.preset_manager = preset_manager
    tab.setup_ui()
    tab.on_options_changed(options)

    # Run
    item = tab.window.create_preset_tree.preset_to_item.get(preset.uuid)
    # assert item.parent().text(0) == "1"
    if not game.data.development_state.can_view(allow_experimental):
        assert item is None
    else:
        tab.window.create_preset_tree.selectionModel().reset()
        item.setSelected(True)

        # Assert
        assert tab._current_preset_data.get_preset() == preset.get_preset()


def test_generate_new_seed(tab, preset_manager, mocker):
    # Setup
    mock_randint: MagicMock = mocker.patch("random.randint", return_value=12341234)

    tab.window.create_preset_tree = MagicMock()
    tab.window.create_preset_tree.current_preset_data = preset_manager.default_preset
    tab.generate_seed_from_permalink = MagicMock()

    spoiler = MagicMock(spec=bool)
    retries = MagicMock(spec=int)

    # Run
    tab._generate_new_seed(spoiler, retries)

    # Assert
    tab.generate_seed_from_permalink.assert_called_once_with(
        Permalink.from_parameters(
            GeneratorParameters(
                seed_number=12341234,
                spoiler=spoiler,
                presets=[preset_manager.default_preset.get_preset()],
            )
        ), retries=retries
    )
    mock_randint.assert_called_once_with(0, 2 ** 31)
