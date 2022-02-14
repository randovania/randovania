from unittest.mock import MagicMock

from PySide2 import QtGui

from randovania.gui.widgets.randovania_help_widget import RandovaniaHelpWidget


def test_on_first_show(skip_qtbot):
    # Setup
    widget = RandovaniaHelpWidget()

    # Run
    widget._on_first_show()

    # Assert
    # Just testing it successfully runs


def test_showEvent_twice(skip_qtbot):
    # Setup
    widget = RandovaniaHelpWidget()
    widget._on_first_show = MagicMock()

    # Run
    widget.showEvent(QtGui.QShowEvent())
    widget.showEvent(QtGui.QShowEvent())

    # Assert
    widget._on_first_show.assert_called_once_with()
