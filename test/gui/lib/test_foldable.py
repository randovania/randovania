from __future__ import annotations

import pytest

from randovania.gui.widgets.foldable import Foldable


def test_foldable_initial_state(skip_qtbot):
    # Setup & Run
    foldable = Foldable(None, "My foldable title", False)
    foldable_2 = Foldable(None, "")

    skip_qtbot.addWidget(foldable)
    skip_qtbot.addWidget(foldable_2)

    # Assert
    assert foldable._toggle_button.text() == "My foldable title"
    assert not foldable._folded
    assert foldable_2._folded


def test_foldable_actions(skip_qtbot):
    # Setup
    foldable = Foldable(None, "My foldable title")

    skip_qtbot.addWidget(foldable)

    # Run & Assert
    foldable._unfold()
    assert not foldable._folded
    assert not foldable._content_area.isHidden()

    foldable._fold()
    assert foldable._folded
    assert foldable._content_area.isHidden()


def test_foldable_title_ui_property(skip_qtbot) -> None:
    foldable = Foldable(None)
    skip_qtbot.addWidget(foldable)

    assert foldable.setProperty("title", "Title from UI file")
    assert foldable._toggle_button.text() == "Title from UI file"
    assert foldable.property("title") == "Title from UI file"


@pytest.mark.parametrize("folded", [False, True])
def test_foldable_folded_ui_property(skip_qtbot, folded: bool) -> None:
    foldable = Foldable(None)
    skip_qtbot.addWidget(foldable)

    assert foldable.setProperty("folded", folded)
    assert foldable.property("folded") is folded
    assert foldable._folded is folded
    assert foldable._content_area.isHidden() is folded
