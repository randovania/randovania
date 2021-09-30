import pytest
from randovania.gui.lib.foldable import Foldable


def test_foldable_initial_state(skip_qtbot):
    # Setup & Run
    foldable = Foldable("My foldable title", False)
    foldable_2 = Foldable("")
    
    skip_qtbot.addWidget(foldable)
    skip_qtbot.addWidget(foldable_2)

    # Assert
    assert foldable._toggleButton.text() == "My foldable title"
    assert not foldable._folded
    assert foldable_2._folded

def test_foldable_actions(skip_qtbot):
    # Setup
    foldable = Foldable("My foldable title")

    skip_qtbot.addWidget(foldable)

    # Run & Assert
    foldable._unfold()
    assert not foldable._folded
    assert not foldable._contentArea.isHidden()
    
    foldable._fold()
    assert foldable._folded
    assert foldable._contentArea.isHidden()