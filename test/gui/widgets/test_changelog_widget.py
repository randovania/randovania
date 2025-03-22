from __future__ import annotations

from typing import TYPE_CHECKING, cast

import pytest

from randovania.gui.widgets.changelog_widget import ChangeLogWidget
from randovania.gui.widgets.delayed_text_label import DelayedTextLabel

if TYPE_CHECKING:
    from PySide6 import QtWidgets
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


@pytest.mark.filterwarnings("ignore:Failed to disconnect .* from signal:RuntimeWarning")
async def test_create(skip_qtbot: QtBot) -> None:
    # Setup
    widget = ChangeLogWidget(CUSTOM_LOGS)
    skip_qtbot.addWidget(widget)

    # Assert
    with skip_qtbot.waitSignal(widget.done_fetching_data):
        await widget.setup_labels()
        assert widget.select_version.count() == EXPECTED_VERSIONS_COUNT

    for i in range(1, EXPECTED_VERSIONS_COUNT + 1):
        assert widget.select_version.itemText(i - 1) == CUSTOM_LOGS_KEYS[i - 1]

    widget.select_version.setCurrentIndex(0)
    qscroll_0 = cast("QtWidgets.QScrollArea", widget.changelog.currentWidget())
    qframe_0 = cast("QtWidgets.QFrame", qscroll_0.widget())
    qlabel_0 = cast("DelayedTextLabel", qframe_0.findChild(DelayedTextLabel))
    assert qlabel_0.text() == "Foo"

    widget.select_version.setCurrentIndex(1)
    qscroll_1 = cast("QtWidgets.QScrollArea", widget.changelog.currentWidget())
    qsrame_1 = cast("QtWidgets.QFrame", qscroll_1.widget())
    qlabel_1 = cast("DelayedTextLabel", qsrame_1.findChild(DelayedTextLabel))
    assert qlabel_1.text() == "Bar"

    widget.select_version.setCurrentIndex(2)
    qscroll_2 = cast("QtWidgets.QScrollArea", widget.changelog.currentWidget())
    qframe_2 = cast("QtWidgets.QFrame", qscroll_2.widget())
    qlabel_2_list = cast("list[DelayedTextLabel]", qframe_2.findChildren(DelayedTextLabel))
    assert len(qframe_2.findChildren(DelayedTextLabel)) == 3
    assert qlabel_2_list[0].text() == "### Testing ^_^"
    assert not qlabel_2_list[1].pixmap().isNull()
    assert qlabel_2_list[2].text() == "Text after image"

    widget.select_version.setCurrentIndex(3)
    qscroll_3 = cast("QtWidgets.QScrollArea", widget.changelog.currentWidget())
    qframe_3 = cast("QtWidgets.QFrame", qscroll_3.widget())
    qlabel_3_list = cast("list[DelayedTextLabel]", qframe_3.findChildren(DelayedTextLabel))
    assert len(qframe_3.findChildren(DelayedTextLabel)) == 5
    assert qlabel_3_list[0].text() == "### Get ready for 2 images!!!\nFirst:"
    assert not qlabel_3_list[1].pixmap().isNull()
    assert qlabel_3_list[2].text() == "Second:"
    assert not qlabel_3_list[3].pixmap().isNull()
    assert qlabel_3_list[4].text() == "blah blah blah"
