from __future__ import annotations

from typing import TYPE_CHECKING, cast

from PySide6 import QtWidgets

from randovania.gui.widgets.changelog_widget import ChangeLogWidget
from randovania.gui.widgets.delayed_text_label import DelayedTextLabel

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot

IMG_LINK = "https://user-images.githubusercontent.com/884928/42738464-8a68e82a-885a-11e8-8b05-a2af0b8ad9e9.png"

IMG_TAG = f"![image]({IMG_LINK})"

CUSTOM_LOGS = {
    "1.0": "Foo",
    "2.0": "Bar",
    "3.0": f"### Testing ^_^\n{IMG_TAG}\nText after image",
    "4.0": f"### Get ready for 2 images!!!\nFirst:\n{IMG_TAG}\nSecond:\n{IMG_TAG}\nblah blah blah",
}

CUSTOM_LOGS_KEYS = list(CUSTOM_LOGS.keys())

EXPECTED_VERSIONS_COUNT = len(CUSTOM_LOGS_KEYS)


def test_create(skip_qtbot: QtBot):
    # Setup
    widget = ChangeLogWidget(CUSTOM_LOGS)
    skip_qtbot.addWidget(widget)

    with skip_qtbot.waitSignal(widget.doneFetchingData):
        # Assert
        assert widget.select_version.count() == EXPECTED_VERSIONS_COUNT

        for i in range(1, EXPECTED_VERSIONS_COUNT + 1):
            assert widget.select_version.itemText(i - 1) == CUSTOM_LOGS_KEYS[i - 1]

        widget.select_version.setCurrentIndex(0)
        qScroll0 = cast(QtWidgets.QScrollArea, widget.changelog.currentWidget())
        qFrame0 = cast(QtWidgets.QFrame, qScroll0.widget())
        qLabel0 = cast(DelayedTextLabel, qFrame0.findChild(DelayedTextLabel))
        assert qLabel0.text() == "Foo"

        widget.select_version.setCurrentIndex(1)
        qScroll1 = cast(QtWidgets.QScrollArea, widget.changelog.currentWidget())
        qFrame1 = cast(QtWidgets.QFrame, qScroll1.widget())
        qLabel1 = cast(DelayedTextLabel, qFrame1.findChild(DelayedTextLabel))
        assert qLabel1.text() == "Bar"

        widget.select_version.setCurrentIndex(2)
        qScroll2 = cast(QtWidgets.QScrollArea, widget.changelog.currentWidget())
        qFrame2 = cast(QtWidgets.QFrame, qScroll2.widget())
        qLabel2_list = cast(list[DelayedTextLabel], qFrame2.findChildren(DelayedTextLabel))
        assert len(qFrame2.findChildren(DelayedTextLabel)) == 3
        assert qLabel2_list[0].text() == "### Testing ^_^"
        assert not qLabel2_list[1].pixmap().isNull()
        assert qLabel2_list[2].text() == "Text after image"

        widget.select_version.setCurrentIndex(3)
        qScroll3 = cast(QtWidgets.QScrollArea, widget.changelog.currentWidget())
        qFrame3 = cast(QtWidgets.QFrame, qScroll3.widget())
        qLabel3_list = cast(list[DelayedTextLabel], qFrame3.findChildren(DelayedTextLabel))
        assert len(qFrame3.findChildren(DelayedTextLabel)) == 5
        assert qLabel3_list[0].text() == "### Get ready for 2 images!!!\nFirst:"
        assert not qLabel3_list[1].pixmap().isNull()
        assert qLabel3_list[2].text() == "Second:"
        assert not qLabel3_list[3].pixmap().isNull()
        assert qLabel3_list[4].text() == "blah blah blah"
