import dataclasses
import datetime
import json
from unittest.mock import MagicMock

from randovania.gui.dialog.preset_history_dialog import PresetHistoryDialog
from randovania.layout.base.damage_strictness import LayoutDamageStrictness
from randovania.layout.versioned_preset import VersionedPreset


def test_select_item(skip_qtbot, default_preset):
    # Setup
    versioned_preset = VersionedPreset.with_preset(default_preset)
    old_preset = dataclasses.replace(
        default_preset,
        configuration=dataclasses.replace(
            default_preset.configuration,
            damage_strictness=LayoutDamageStrictness.STRICT,
        )
    )

    preset_manager = MagicMock()
    preset_manager.get_previous_versions.return_value = [
        (datetime.datetime(2020, 10, 1, 10, 20), b"ABCDEF"),
    ]
    preset_manager.get_previous_version.return_value = json.dumps(VersionedPreset.with_preset(old_preset).as_json)

    dialog = PresetHistoryDialog(preset_manager, versioned_preset)
    skip_qtbot.add_widget(dialog)

    # Run
    preset_manager.get_previous_version.assert_called_once_with(versioned_preset, b"ABCDEF")
    assert dialog.version_widget.count() == 2

    # Initially the dialog has nothing selected
    assert dialog.selected_preset() is None
    assert not dialog.accept_button.isEnabled()

    # Select the second row
    dialog.version_widget.setCurrentIndex(dialog.version_widget.model().index(1))
    assert dialog.selected_preset() == old_preset
    assert dialog.accept_button.isEnabled()
