from typing import List

from PySide2.QtWidgets import QDialog

from randovania.game_description.world.world import World
from randovania.gui import game_specific_gui
from randovania.gui.generated.logic_settings_window_ui import Ui_LogicSettingsWindow
from randovania.gui.lib import common_qt_lib
from randovania.gui.lib.window_manager import WindowManager
from randovania.gui.preset_settings.preset_tab import PresetTab
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.preset import Preset

def dark_world_flags(world: World):
    yield False
    if world.dark_name is not None:
        yield True


class LogicSettingsWindow(QDialog, Ui_LogicSettingsWindow):
    _tabs: List[PresetTab]
    _editor: PresetEditor

    def __init__(self, window_manager: WindowManager, editor: PresetEditor):
        super().__init__()
        self.setupUi(self)
        common_qt_lib.set_default_window_icon(self)

        self._editor = editor
        self._tabs = game_specific_gui.preset_editor_tabs_for(editor, window_manager)

        for extra_tab in self._tabs:
            if extra_tab.uses_patches_tab:
                parent_tab = self.patches_tab_widget
            else:
                parent_tab = self.logic_tab_widget
            parent_tab.addTab(extra_tab, extra_tab.tab_title)

        self.name_edit.textEdited.connect(self._edit_name)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

    # Options
    def on_preset_changed(self, preset: Preset):
        common_qt_lib.set_edit_if_different(self.name_edit, preset.name)
        for extra_tab in self._tabs:
            extra_tab.on_preset_changed(preset)

    def _edit_name(self, value: str):
        with self._editor as editor:
            editor.name = value
