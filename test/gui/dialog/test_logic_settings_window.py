from randovania.gui.dialog.logic_settings_window import LogicSettingsWindow
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.layout_configuration import LayoutConfiguration
from randovania.layout.patcher_configuration import PatcherConfiguration
from randovania.layout.preset import Preset


def test_on_preset_changed(skip_qtbot, preset_manager):
    # Setup
    editor = PresetEditor(preset_manager.default_preset)
    window = LogicSettingsWindow(None, editor)

    # Run
    window.on_preset_changed(editor.create_custom_preset_with())
