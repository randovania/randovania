from PySide6 import QtGui

from randovania.gui.widgets.delayed_text_label import DelayedTextLabel


def test_set_after_show(skip_qtbot):
    # Setup
    label = DelayedTextLabel()
    skip_qtbot.addWidget(label)

    label.setText("Foo")
    assert label.text() == "Foo"
    assert label._delayed_text == "Foo"
    assert not label._already_shown

    label.showEvent(QtGui.QShowEvent())

    assert label.text() == "Foo"
    assert label._delayed_text is None
    assert label._already_shown
