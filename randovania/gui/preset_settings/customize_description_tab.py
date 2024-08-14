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
    def starts_new_header(cls) -> bool:
        return True

    def on_preset_changed(self, preset: Preset):
        self.description_edit.setText(preset.description)

    def _edit_description(self):
        with self._editor as editor:
            editor.description = self.description_edit.toPlainText()
