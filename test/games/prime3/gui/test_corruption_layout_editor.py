from __future__ import annotations

from randovania.games.prime3.gui.corruption_layout_editor import CorruptionLayoutEditor


def test_construct(skip_qtbot):
    expected = (
        "00xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx3b95e"
    )
    editor = CorruptionLayoutEditor()
    skip_qtbot.addWidget(editor)
    assert editor.layout_edit.text() == expected
