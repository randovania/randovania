from randovania.gui.dialog.logic_settings_window import LogicSettingsWindow
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.layout_configuration import LayoutConfiguration
from randovania.layout.patcher_configuration import PatcherConfiguration
from randovania.layout.preset import Preset


def test_on_preset_changed(skip_qtbot):
    # Setup
    editor = PresetEditor(
        Preset(
            name="A name",
            description="A preset that was customized.",
            base_preset_name=None,
            patcher_configuration=PatcherConfiguration.default(),
            layout_configuration=LayoutConfiguration.default(),
        )
    )
    window = LogicSettingsWindow(None, editor)

    # Run
    window.on_preset_changed(editor.create_custom_preset_with())
