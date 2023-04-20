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
        self.setupUi(self)

        # Signals
        for f in _FIELDS:
            self._add_persist_option(getattr(self, f"{f}_check"), f)

        signal_handling.on_checked(
            self.consistent_raven_beak_damage_table_check,
            self._on_consistent_raven_beak_damage_table_changed)

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

    def _on_consistent_raven_beak_damage_table_changed(self, value: bool):
        with self._editor as editor:
            editor.set_configuration_field(
                "consistent_raven_beak_damage_table",
                DreadRavenBeakDamageMode.BUFF_FINAL if value else DreadRavenBeakDamageMode.NERF_ALL)

    def on_preset_changed(self, preset: Preset):
        config = typing.cast(DreadConfiguration, preset.configuration)
        for f in _FIELDS:
            typing.cast(QtWidgets.QCheckBox, getattr(self, f"{f}_check")).setChecked(getattr(config, f))
        self.consistent_raven_beak_damage_table_check.setChecked(not config.consistent_raven_beak_damage_table.is_default)
