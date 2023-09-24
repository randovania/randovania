from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.gui.widgets.changelog_widget import ChangeLogWidget

if TYPE_CHECKING:
    from PySide6 import QtWidgets


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
    qScroll: QtWidgets.QScrollArea = widget.changelog.currentWidget()
    qLabel: QtWidgets.QLabel = qScroll.widget()
    assert qLabel.text() == "Foo"

    widget.select_version.setCurrentIndex(1)
    qScroll: QtWidgets.QScrollArea = widget.changelog.currentWidget()
    qLabel: QtWidgets.QLabel = qScroll.widget()
    assert qLabel.text() == "Bar"
