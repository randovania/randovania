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


def test_drop_random_event(default_main_window: MainWindow,
                           qtbot,
                           ):
    # Creating a window should not fail
    pass
