from __future__ import annotations

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
    qScroll0 = widget.changelog.currentWidget()
    qLabel0 = qScroll0.widget()
    assert qLabel0.text() == "Foo"

    widget.select_version.setCurrentIndex(1)
    qScroll1 = widget.changelog.currentWidget()
    qLabel1 = qScroll1.widget()
    assert qLabel1.text() == "Bar"
