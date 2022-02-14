import json

from randovania.games.super_metroid.gui.preset_settings.super_patches_tab import PresetSuperPatchConfiguration
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.preset import Preset


def test_elements_init(skip_qtbot, test_files_dir):
    # Set up and initialize patches tab
    preset_file = test_files_dir.joinpath("presets/super_test_preset.rdvpreset").open()
    preset_dict = json.load(preset_file)
    preset_file.close()
    preset = Preset.from_json_dict(preset_dict)
    editor = PresetEditor(preset)
    super_patches_tab = PresetSuperPatchConfiguration(editor)
    skip_qtbot.addWidget(super_patches_tab)

    # Test whether visual elements are initialized correctly
    patches = (preset_dict["configuration"])["patches"]
    for field_name, checkbox in super_patches_tab.checkboxes.items():
        assert checkbox.isChecked() == patches[field_name]
