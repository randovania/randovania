from __future__ import annotations

from typing import cast

from PySide6 import QtWidgets

from randovania.gui.widgets.changelog_widget import ChangeLogWidget


def test_create(skip_qtbot):
    # Setup
    widget = ChangeLogWidget(
        {
            "1.0": "Foo",
            "2.0": "Bar",
        }
    )
    skip_qtbot.addWidget(widget)

    # Assert
    assert widget.select_version.count() == 2
    assert widget.select_version.itemText(0) == "1.0"
    assert widget.select_version.itemText(1) == "2.0"

    widget.select_version.setCurrentIndex(0)
    qScroll0 = cast(QtWidgets.QScrollArea, widget.changelog.currentWidget())
    qLabel0 = cast(QtWidgets.QLabel, qScroll0.widget())
    assert qLabel0.text() == "Foo"

    widget.select_version.setCurrentIndex(1)
    qScroll1 = cast(QtWidgets.QScrollArea, widget.changelog.currentWidget())
    qLabel1 = cast(QtWidgets.QLabel, qScroll1.widget())
    assert qLabel1.text() == "Bar"
