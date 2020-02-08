from pathlib import Path
from typing import Union
from unittest.mock import MagicMock, patch

import pytest

from randovania.gui.main_window import MainWindow
from randovania.interface_common.options import Options
from randovania.interface_common.preset_manager import PresetManager


def create_window(options: Union[Options, MagicMock],
                  preset_manager: PresetManager) -> MainWindow:
    return MainWindow(options, preset_manager, False)


@pytest.fixture(name="default_main_window")
def _default_main_window(skip_qtbot, preset_manager) -> MainWindow:
    return create_window(Options(MagicMock()), preset_manager)


def test_drop_random_event(default_main_window: MainWindow,
                           ):
    # Creating a window should not fail
    pass
