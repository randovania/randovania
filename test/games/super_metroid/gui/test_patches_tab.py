from randovania.games.super_metroid.gui.preset_settings.super_patches_tab import PresetSuperPatchConfiguration
from randovania.games.super_metroid.layout.super_metroid_configuration import SuperMetroidConfiguration
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.versioned_preset import VersionedPreset


def test_elements_init(skip_qtbot, test_files_dir):
    preset_path = test_files_dir.joinpath("presets/super_test_preset.rdvpreset")
    preset = VersionedPreset.from_file_sync(preset_path).get_preset()
    assert isinstance(preset.configuration, SuperMetroidConfiguration)

    editor = PresetEditor(preset)
    super_patches_tab = PresetSuperPatchConfiguration(editor)
    skip_qtbot.addWidget(super_patches_tab)

    # Test whether visual elements are initialized correctly
    patches = preset.configuration.patches
    for field_name, checkbox in super_patches_tab.checkboxes.items():
        assert checkbox.isChecked() == getattr(patches, field_name)
