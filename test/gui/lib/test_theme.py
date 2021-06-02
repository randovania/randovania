from unittest.mock import MagicMock

import pytest
from PySide2 import QtGui

from randovania.gui.lib import theme


def test_set_dark_theme_no_change(skip_qtbot):
    theme._current_dark_theme = False
    theme.set_dark_theme(False)


@pytest.mark.parametrize("active", [False, True])
def test_set_dark_theme_change(skip_qtbot, active, mocker):
    import qdarkstyle
    mock_load_stylesheet: MagicMock = mocker.patch("qdarkstyle.load_stylesheet", return_value="")

    app = MagicMock()
    app.palette.return_value = QtGui.QPalette()

    theme._current_dark_theme = not active
    theme.set_dark_theme(active, app)

    mock_load_stylesheet.assert_called_once_with(qt_api='pyside2',
                                                 palette=qdarkstyle.DarkPalette if active
                                                 else qdarkstyle.LightPalette)
    app.setStyleSheet.assert_called_once()
    app.setPalette.assert_called_once()
