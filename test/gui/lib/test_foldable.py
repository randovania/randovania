from __future__ import annotations

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
