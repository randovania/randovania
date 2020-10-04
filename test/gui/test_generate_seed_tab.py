import pytest
from PySide2 import QtWidgets
from mock import MagicMock

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
