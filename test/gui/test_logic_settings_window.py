from unittest.mock import MagicMock

import pytest

from randovania.gui.logic_settings_window import LogicSettingsWindow
from randovania.interface_common.options import Options

pytestmark = pytest.mark.skipif(
    pytest.config.option.skip_gui_tests,
    reason="skipped due to --skip-gui-tests")


def test_on_options_changed(qtbot):
    # Setup
    options = Options(MagicMock())
    window = LogicSettingsWindow(None, options)

    # Run
    window.on_options_changed(options)
