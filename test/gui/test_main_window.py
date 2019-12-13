from pathlib import Path
from typing import Union
from unittest.mock import MagicMock, patch

import pytest

from randovania.gui.main_window import MainWindow
from randovania.interface_common.options import Options


def create_window(options: Union[Options, MagicMock]) -> MainWindow:
    return MainWindow(options, False)


@pytest.fixture(name="default_main_window")
def _default_main_window(skip_qtbot) -> MainWindow:
    return create_window(Options(MagicMock()))


def test_drop_random_event(default_main_window: MainWindow,
                           ):
    # Creating a window should not fail
    pass
