from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from pynput import keyboard
from PySide6 import QtCore, QtGui, QtWidgets

from randovania.gui.generated.hotkeys_widget_ui import Ui_HotkeyWidget
from randovania.gui.lib import common_qt_lib
from randovania.lib.hotkeys import Hotkey

if TYPE_CHECKING:
    from randovania.interface_common.options import Options


from enum import Enum


class HotkeyType(Enum):
    START_FINISH = "start_finish"
    PAUSE = "pause"


class HotkeysWidget(QtWidgets.QDialog, Ui_HotkeyWidget):
    _options: Options
    start_finish_key: int | str
    keyboard_listener: keyboard.Listener | None

    def __init__(self, options: Options):
        super().__init__()
        self._options = options
        self.setupUi(self)
        common_qt_lib.set_default_window_icon(self)

        self.start_finish_button.clicked.connect(self._on_start_finish_clicked)
        self.pause_button.clicked.connect(self._on_pause_clicked)
        self.start_finish_button.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.pause_button.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.dialog_buttons.button(QtWidgets.QDialogButtonBox.StandardButton.Reset).clicked.connect(
            self._on_reset_clicked
        )
        self.keyboard_listener = None

        self._refresh_buttons_ui()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self._refresh_buttons_ui()
        super().closeEvent(event)

    def _on_start_finish_clicked(self) -> None:
        self._prompt_key(HotkeyType.START_FINISH)

    def _on_pause_clicked(self) -> None:
        self._prompt_key(HotkeyType.PAUSE)

    def _on_reset_clicked(self) -> None:
        with self._options as options:
            options.hotkeys = dataclasses.replace(options.hotkeys, pause_hotkey=None, start_finish_hotkey=None)
        self._refresh_buttons_ui()

    def _prompt_key(self, hotkey_type: HotkeyType) -> None:
        if hotkey_type == HotkeyType.START_FINISH:
            self.start_finish_button.setText("Press any key...")
            self.start_finish_button.setEnabled(False)
            self.pause_button.setEnabled(False)
        elif hotkey_type == HotkeyType.PAUSE:
            self.pause_button.setText("Press any key...")
            self.start_finish_button.setEnabled(False)
            self.pause_button.setEnabled(False)
        self._listen_for_key(hotkey_type)

    def _refresh_buttons_ui(self) -> None:
        options = self._options
        start_finish_hotkey = options.hotkeys.start_finish_hotkey
        pause_hotkey = options.hotkeys.pause_hotkey

        self.start_finish_button.setEnabled(True)
        self.pause_button.setEnabled(True)

        if start_finish_hotkey:
            self.start_finish_button.setText(start_finish_hotkey.user_friendly_str())
        else:
            self.start_finish_button.setText("Not Set")
        if pause_hotkey:
            self.pause_button.setText(pause_hotkey.user_friendly_str())
        else:
            self.pause_button.setText("Not Set")

        if self.keyboard_listener:
            self.keyboard_listener.stop()

    def _get_key_name(self, key: keyboard.Key | keyboard.KeyCode) -> str:
        # 'F1' etc. are passed as Key and don't have a virtual key code
        if isinstance(key, keyboard.Key):
            return key.name
        if isinstance(key, keyboard.KeyCode):
            # common characters such as "a", "w" etc. are received as KeyCode with char but numpad
            # keys are only passed with a virtual key code
            return str(key.vk)

    def _on_press(self, key: keyboard.Key | keyboard.KeyCode | None, hotkey_type: HotkeyType) -> None:
        if key is None:
            return

        entry: Hotkey = Hotkey(
            self._get_key_name(key),
        )

        # don't allow escape because it closes the ui
        if entry.name_or_vk != keyboard.Key.esc.name:
            with self._options as options:
                if hotkey_type == HotkeyType.START_FINISH:
                    options.hotkeys = dataclasses.replace(options.hotkeys, start_finish_hotkey=entry)
                elif hotkey_type == HotkeyType.PAUSE:
                    options.hotkeys = dataclasses.replace(options.hotkeys, pause_hotkey=entry)

        self._refresh_buttons_ui()

    def _listen_for_key(self, hotkey_type: HotkeyType) -> None:
        self.keyboard_listener = keyboard.Listener(on_press=lambda key: self._on_press(key, hotkey_type=hotkey_type))
        self.keyboard_listener.start()
