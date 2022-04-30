import typing

from PySide6 import QtWidgets

from randovania.games.prime1.layout.prime_configuration import LayoutCutsceneMode, RoomRandoMode
from randovania.gui.generated.preset_prime_patches_ui import Ui_PresetPrimePatches
from randovania.gui.lib import signal_handling
from randovania.gui.preset_settings.preset_tab import PresetTab
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.preset import Preset

_FIELDS = [
    "warp_to_start",
    "main_plaza_door",
    "backwards_frigate",
    "backwards_labs",
    "backwards_upper_mines",
    "backwards_lower_mines",
    "phazon_elite_without_dynamo",
    "qol_game_breaking",
    "qol_pickup_scans",
    "small_samus",
    "large_samus",
    "shuffle_item_pos",
    "items_every_room",
    "random_boss_sizes",
    "no_doors",
    "spring_ball",
    "deterministic_idrone",
    "deterministic_maze",
]


class PresetPrimePatches(PresetTab, Ui_PresetPrimePatches):
    def __init__(self, editor: PresetEditor):
        super().__init__(editor)
        self.setupUi(self)

        self.description_label.setText(self.description_label.text().replace("color:#0000ff;", ""))

        # Signals
        self.cutscene_combo.setItemData(0, LayoutCutsceneMode.ORIGINAL)
        self.cutscene_combo.setItemData(1, LayoutCutsceneMode.COMPETITIVE)
        self.cutscene_combo.setItemData(2, LayoutCutsceneMode.MINOR)
        self.cutscene_combo.setItemData(3, LayoutCutsceneMode.MAJOR)
        signal_handling.on_combo(self.cutscene_combo, self._on_cutscene_changed)
        self.room_rando_combo.setItemData(0, RoomRandoMode.NONE)
        self.room_rando_combo.setItemData(1, RoomRandoMode.ONE_WAY)
        self.room_rando_combo.setItemData(2, RoomRandoMode.TWO_WAY)
        signal_handling.on_combo(self.room_rando_combo, self._on_room_rando_changed)
        for f in _FIELDS:
            self._add_persist_option(getattr(self, f"{f}_check"), f)

        signal_handling.on_checked(self.small_samus_check, self._on_small_samus_changed)
        signal_handling.on_checked(self.large_samus_check, self._on_large_samus_changed)

        self.superheated_slider.valueChanged.connect(self._on_slider_changed)
        self.submerged_slider.valueChanged.connect(self._on_slider_changed)

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

    def _on_small_samus_changed(self, value: bool):
        with self._editor as editor:
            editor.set_configuration_field("small_samus", value)
            if value:
                editor.set_configuration_field("large_samus", False)

    def _on_large_samus_changed(self, value: bool):
        with self._editor as editor:
            editor.set_configuration_field("large_samus", value)
            if value:
                editor.set_configuration_field("small_samus", False)

    def _on_cutscene_changed(self, value: LayoutCutsceneMode):
        with self._editor as editor:
            editor.set_configuration_field("qol_cutscenes", value)

    def _on_room_rando_changed(self, value: RoomRandoMode):
        with self._editor as editor:
            editor.set_configuration_field("room_rando", value)

    def on_preset_changed(self, preset: Preset):
        config = preset.configuration
        for f in _FIELDS:
            typing.cast(QtWidgets.QCheckBox, getattr(self, f"{f}_check")).setChecked(getattr(config, f))
        signal_handling.combo_set_to_value(self.cutscene_combo, config.qol_cutscenes)
        signal_handling.combo_set_to_value(self.room_rando_combo, config.room_rando)
        self.superheated_slider.setValue(preset.configuration.superheated_probability)
        self.submerged_slider.setValue(preset.configuration.submerged_probability)
        self._on_slider_changed()

    def _update_editor(self):
        with self._editor as editor:
            editor.set_configuration_field(
                "superheated_probability",
                self.superheated_slider.value()
            )
            editor.set_configuration_field(
                "submerged_probability",
                self.submerged_slider.value()
            )

    def _on_slider_changed(self):
        self.superheated_slider_label.setText(f"{self.superheated_slider.value() / 10.0:.1f}%")
        self.submerged_slider_label.setText(f"{self.submerged_slider.value() / 10.0:.1f}%")
        self._update_editor()
