from randovania.gui.corruption_layout_editor import CorruptionLayoutEditor


def test_construct(skip_qtbot):
    expected = ("00xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx3b95e")
    editor = CorruptionLayoutEditor()
    assert editor.layout_edit.text() == expected
