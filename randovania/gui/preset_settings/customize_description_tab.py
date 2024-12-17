from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.gui.generated.preset_customize_description_ui import Ui_PresetCustomizeDescription
from randovania.gui.preset_settings.preset_tab import PresetTab

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


class PresetCustomizeDescription(PresetTab, Ui_PresetCustomizeDescription):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        self.setupUi(self)

        self.description_edit.textChanged.connect(self._edit_description)

    @classmethod
    def tab_title(cls) -> str:
        return "Preset Description"

    @classmethod
    def header_name(cls) -> str | None:
        return "Preset Info"

    def on_preset_changed(self, preset: Preset) -> None:
        # to set the visible cursor you must use setTextCursor but at
        # the same time the "cursor" object gets updated => save the old position, set it
        # in the cursor and then use "setTextCursor"
        cursor = self.description_edit.textCursor()
        cursor_pos = cursor.position()
        self.description_edit.setText(preset.description)
        cursor.setPosition(cursor_pos)
        self.description_edit.setTextCursor(cursor)

    def _edit_description(self) -> None:
        with self._editor as editor:
            editor.description = self.description_edit.toPlainText()
