from __future__ import annotations

import typing
from typing import TYPE_CHECKING

from randovania.games.am2r.gui.generated.preset_am2r_gameplay_ui import Ui_PresetAM2RGameplay
from randovania.games.am2r.layout.am2r_configuration import AM2RConfiguration
from randovania.gui.lib import signal_handling
from randovania.gui.preset_settings.preset_tab import PresetTab

if TYPE_CHECKING:
    from PySide6 import QtWidgets

    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


class PresetAM2RGameplay(PresetTab, Ui_PresetAM2RGameplay):
    _CHECKBOX_FIELDS = [
        "skip_cutscenes",
        "skip_save_cutscene",
        "skip_item_cutscenes",
        "fusion_mode",
        "vertically_flip_gameplay",
        "horizontally_flip_gameplay",
    ]

    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        self.setupUi(self)

        self.energy_tank_capacity_spin_box.valueChanged.connect(self._persist_tank_capacity)
        self.first_suit_spin_box.valueChanged.connect(self._persist_first_suit_dr)
        self.second_suit_spin_box.valueChanged.connect(self._persist_second_suit_dr)

        # Checkbox Signals
        for f in self._CHECKBOX_FIELDS:
            self._add_checkbox_persist_option(getattr(self, f"{f}_check"), f)

    @classmethod
    def tab_title(cls) -> str:
        return "Gameplay Changes"

    @classmethod
    def header_name(cls) -> str | None:
        return None

    def on_preset_changed(self, preset: Preset) -> None:
        config = preset.configuration
        assert isinstance(config, AM2RConfiguration)
        self.energy_tank_capacity_spin_box.setValue(config.energy_per_tank)
        self.first_suit_spin_box.setValue(config.first_suit_dr)
        self.second_suit_spin_box.setValue(config.second_suit_dr)
        for f in self._CHECKBOX_FIELDS:
            typing.cast("QtWidgets.QCheckBox", getattr(self, f"{f}_check")).setChecked(getattr(config, f))

    def _persist_tank_capacity(self) -> None:
        with self._editor as editor:
            editor.set_configuration_field("energy_per_tank", int(self.energy_tank_capacity_spin_box.value()))

    def _add_checkbox_persist_option(self, check: QtWidgets.QCheckBox, attribute_name: str) -> None:
        def persist(value: bool) -> None:
            with self._editor as editor:
                editor.set_configuration_field(attribute_name, value)

        signal_handling.on_checked(check, persist)

    def _persist_first_suit_dr(self) -> None:
        with self._editor as editor:
            editor.set_configuration_field("first_suit_dr", int(self.first_suit_spin_box.value()))
        self.second_suit_spin_box.setMinimum(self.first_suit_spin_box.value())

    def _persist_second_suit_dr(self) -> None:
        with self._editor as editor:
            editor.set_configuration_field("second_suit_dr", int(self.second_suit_spin_box.value()))
        self.first_suit_spin_box.setMaximum(self.second_suit_spin_box.value())
