from __future__ import annotations

import typing

from randovania.games.prime1.gui.generated.preset_prime_chaos_ui import Ui_PresetPrimeChaos
from randovania.games.prime1.layout.prime_configuration import PrimeConfiguration, RoomRandoMode
from randovania.gui.lib import signal_handling
from randovania.gui.preset_settings.preset_tab import PresetTab

if typing.TYPE_CHECKING:
    from PySide6 import QtWidgets

    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset

_FIELDS = [
    "legacy_mode",
    "small_samus",
    "large_samus",
    "shuffle_item_pos",
    "items_every_room",
    "random_boss_sizes",
]


class PresetPrimeChaos(PresetTab[PrimeConfiguration], Ui_PresetPrimeChaos):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        self.setupUi(self)

        self.chaos_label.setText(self.chaos_label.text().replace("color:#0000ff;", ""))

        # Signals
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
        return "Chaos Settings"

    @classmethod
    def is_experimental(cls) -> bool:
        return True

    @classmethod
    def header_name(cls) -> str | None:
        return None

    def _add_persist_option(self, check: QtWidgets.QCheckBox, attribute_name: str) -> None:
        def persist(value: bool) -> None:
            with self._editor as editor:
                editor.set_configuration_field(attribute_name, value)

        signal_handling.on_checked(check, persist)

    def _on_small_samus_changed(self, value: bool) -> None:
        with self._editor as editor:
            editor.set_configuration_field("small_samus", value)
            if value:
                editor.set_configuration_field("large_samus", False)

    def _on_large_samus_changed(self, value: bool) -> None:
        with self._editor as editor:
            editor.set_configuration_field("large_samus", value)
            if value:
                editor.set_configuration_field("small_samus", False)

    def _on_room_rando_changed(self, value: RoomRandoMode) -> None:
        with self._editor as editor:
            editor.set_configuration_field("room_rando", value)

    def on_preset_changed(self, preset: Preset[PrimeConfiguration]) -> None:
        config = preset.configuration
        for f in _FIELDS:
            typing.cast("QtWidgets.QCheckBox", getattr(self, f"{f}_check")).setChecked(getattr(config, f))
        signal_handling.set_combo_with_value(self.room_rando_combo, config.room_rando)
        self.superheated_slider.setValue(preset.configuration.superheated_probability)
        self.submerged_slider.setValue(preset.configuration.submerged_probability)
        self._on_slider_changed()

    def _update_editor(self) -> None:
        with self._editor as editor:
            editor.set_configuration_field("superheated_probability", self.superheated_slider.value())
            editor.set_configuration_field("submerged_probability", self.submerged_slider.value())

    def _on_slider_changed(self) -> None:
        self.superheated_slider_label.setText(f"{self.superheated_slider.value() / 10.0:.1f}%")
        self.submerged_slider_label.setText(f"{self.submerged_slider.value() / 10.0:.1f}%")
        self._update_editor()
