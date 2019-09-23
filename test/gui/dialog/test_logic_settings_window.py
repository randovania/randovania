from unittest.mock import MagicMock

from randovania.gui.dialog.logic_settings_window import LogicSettingsWindow
from randovania.interface_common.options import Options


def test_on_options_changed(skip_qtbot):
    # Setup
    options = Options(MagicMock())
    window = LogicSettingsWindow(None, options)

    # Run
    window.on_options_changed(options)
