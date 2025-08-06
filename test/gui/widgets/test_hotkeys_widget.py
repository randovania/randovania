from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

from pynput import keyboard
from PySide6 import QtCore

from randovania.gui.widgets.hotkeys_widget import HotkeysWidget, HotkeyType

if TYPE_CHECKING:
    import pytestqt.qtbot

    from randovania.interface_common.options import Options


def test_hotkeys_widget(skip_qtbot: pytestqt.qtbot.QtBot, options: Options) -> None:
    widget = HotkeysWidget(options)
    widget._listen_for_key = MagicMock()
    skip_qtbot.addWidget(widget)

    # init state
    assert widget.start_finish_button.text() == "Not Set"
    assert widget.pause_button.text() == "Not Set"

    # clicking one button
    skip_qtbot.mouseClick(widget.start_finish_button, QtCore.Qt.MouseButton.LeftButton)
    widget._listen_for_key.assert_called_once()
    assert widget.start_finish_button.text() == "Press any key..."
    assert not widget.start_finish_button.isEnabled()
    assert widget.pause_button.text() == "Not Set"
    assert not widget.pause_button.isEnabled()

    # set key "A" for start_finish hotkey and check the state
    widget._on_press(keyboard.KeyCode(char="a", vk="65"), HotkeyType.START_FINISH)
    assert widget.start_finish_button.text() == "A"
    assert widget.start_finish_button.isEnabled()
    assert widget.pause_button.text() == "Not Set"
    assert widget.pause_button.isEnabled()
    assert options.hotkeys.start_finish_hotkey
    assert options.hotkeys.start_finish_hotkey.name_or_vk == "65"
