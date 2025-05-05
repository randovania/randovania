from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6 import QtCore

from randovania.games.prime_hunters.gui.generated.preset_prime_hunters_force_fields_ui import (
    Ui_PresetHuntersForceFields,
)
from randovania.games.prime_hunters.layout.force_field_configuration import LayoutForceFieldRequirement
from randovania.games.prime_hunters.layout.prime_hunters_configuration import HuntersConfiguration
from randovania.gui.preset_settings.preset_tab import PresetTab

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.games.prime_hunters.layout.force_field_configuration import (
        ForceFieldConfiguration,
    )
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


def _force_field_config(editor: PresetEditor) -> ForceFieldConfiguration:
    config = editor.configuration
    assert isinstance(config, HuntersConfiguration)
    return config.force_field_configuration


class PresetHuntersForceFields(PresetTab, Ui_PresetHuntersForceFields):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        self.setupUi(self)

        self.force_fields_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        self.force_field_randomize_all_radiobutton.toggled.connect(self._on_randomize_all_force_fields_pressed)
        self.force_field_vanilla_radiobutton.toggled.connect(self._on_vanilla_force_fields_pressed)

    @classmethod
    def tab_title(cls) -> str:
        return "Force Fields"

    @classmethod
    def header_name(cls) -> str | None:
        return None

    def _on_randomize_all_force_fields_pressed(self, value: bool) -> None:
        if not value:
            return
        with self._editor as editor:
            editor.set_configuration_field("force_field_configuration", _force_field_config(editor).with_full_random())

    def _on_vanilla_force_fields_pressed(self, value: bool) -> None:
        if not value:
            return
        with self._editor as editor:
            editor.set_configuration_field("force_field_configuration", _force_field_config(editor).with_vanilla())

    def on_preset_changed(self, preset: Preset) -> None:
        assert isinstance(preset.configuration, HuntersConfiguration)
        force_fields = preset.configuration.force_field_configuration
        requirements = force_fields.force_field_requirement
        for node_identifier, requirement in requirements.items():
            if requirement == LayoutForceFieldRequirement.RANDOM:
                self.force_field_randomize_all_radiobutton.setChecked(True)
            else:
                self.force_field_vanilla_radiobutton.setChecked(True)
            break
