from __future__ import annotations

from randovania.gui.widgets.changelog_widget import ChangeLogWidget


def test_create(skip_qtbot):
    # Setup
    widget = ChangeLogWidget(
        {
            "1.0": "Foo",
            "2.0": "Bar",
        },
        {"1.0": "2023-09-16T02:39:26Z", "2.0": "2023-12-15T03:20:05Z"},
    )
    skip_qtbot.addWidget(widget)

    # Assert
    assert widget.select_version.count() == 2
    assert widget.select_version.itemText(0) == "1.0"
    assert widget.select_version.itemText(1) == "2.0"

    widget.select_version.setCurrentIndex(0)
    assert widget.changelog.currentWidget().widget().text() == "2023-09-16T02:39:26Z\n\nFoo"

    widget.select_version.setCurrentIndex(1)
    assert widget.changelog.currentWidget().widget().text() == "2023-12-15T03:20:05Z\n\nBar"
