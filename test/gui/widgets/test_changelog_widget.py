from randovania.gui.widgets.changelog_widget import ChangeLogWidget


def test_create(skip_qtbot):
    # Setup
    widget = ChangeLogWidget({
        "1.0": "Foo",
        "2.0": "Bar",
    })
    skip_qtbot.addWidget(widget)

    # Assert
    assert widget.count() == 2
    assert widget.tabText(0) == "1.0"
    assert widget.tabText(1) == "2.0"
    assert widget.widget(0).widget().text() == "Foo"
    assert widget.widget(1).widget().text() == "Bar"
