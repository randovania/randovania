import typing

from PySide6 import QtWidgets

from randovania.game_description.game_description import GameDescription
from randovania.games.dread.layout.dread_configuration import DreadConfiguration, DreadRavenBeakDamageMode
from randovania.gui.generated.preset_dread_patches_ui import Ui_PresetDreadPatches
from randovania.gui.lib import signal_handling
from randovania.gui.lib.window_manager import WindowManager
from randovania.gui.preset_settings.preset_tab import PresetTab
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.preset import Preset

_FIELDS = [
    "hanubia_shortcut_no_grapple",
    "hanubia_easier_path_to_itorash",
    "x_starts_released",
]


class PresetDreadPatches(PresetTab, Ui_PresetDreadPatches):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        config = typing.cast(DreadConfiguration, editor.configuration)
        self._orig_rb_damage_mode: DreadRavenBeakDamageMode = config.raven_beak_damage_table_handling
        self.setupUi(self)

        # Signals
        for f in _FIELDS:
            self._add_persist_option(getattr(self, f"{f}_check"), f)

        signal_handling.on_checked(
            self.raven_beak_damage_table_handling_check,
            self._on_raven_beak_damage_table_handling_changed)

    @classmethod
    def tab_title(cls) -> str:
        return "Other"

    @classmethod
    def uses_patches_tab(cls) -> bool:
        return True

    def _add_persist_option(self, check: QtWidgets.QCheckBox, attribute_name: str):
        def persist(value: bool):
            with self._editor as editor:
                editor.set_configuration_field(attribute_name, value)

        signal_handling.on_checked(check, persist)

    def _on_raven_beak_damage_table_handling_changed(self, value: bool):
        checked_value = (
            DreadRavenBeakDamageMode.UNMODIFIED
            if self._orig_rb_damage_mode == DreadRavenBeakDamageMode.UNMODIFIED
            else DreadRavenBeakDamageMode.CONSISTENT_HIGH
        )

        with self._editor as editor:
            editor.set_configuration_field(
                "raven_beak_damage_table_handling",
                checked_value if value else DreadRavenBeakDamageMode.CONSISTENT_LOW)

    def on_preset_changed(self, preset: Preset):
        config = typing.cast(DreadConfiguration, preset.configuration)

        for f in _FIELDS:
            typing.cast(QtWidgets.QCheckBox, getattr(self, f"{f}_check")).setChecked(getattr(config, f))

        self._orig_rb_damage_mode = config.raven_beak_damage_table_handling
        self.raven_beak_damage_table_handling_check.setChecked(
            not config.raven_beak_damage_table_handling.is_default)
