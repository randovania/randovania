from __future__ import annotations

import typing
from typing import TYPE_CHECKING

from PySide6 import QtWidgets

from randovania.games.prime1.layout.prime_configuration import PrimeConfiguration
from randovania.gui.lib import signal_handling
from randovania.gui.preset_settings.generation_tab import PresetGeneration

if TYPE_CHECKING:
    from collections.abc import Iterable

    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset

_CHECKBOX_FIELDS = ["pre_place_artifact", "pre_place_phazon"]


class PresetPrimeGeneration(PresetGeneration):
    min_progression_label: QtWidgets.QLabel
    min_progression_spin: QtWidgets.QSpinBox
    pre_place_label: QtWidgets.QLabel
    pre_place_artifact_check: QtWidgets.QCheckBox
    pre_place_phazon_check: QtWidgets.QCheckBox

    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)

        self.min_progression_spin.valueChanged.connect(self._on_spin_changed)
        for f in _CHECKBOX_FIELDS:
            self._add_checkbox_persist_option(getattr(self, f"{f}_check"), f)

    def setupUi(self, obj: QtWidgets.QWidget) -> None:
        super().setupUi(obj)

        self.min_progression_label = QtWidgets.QLabel(
            "Only place artifacts after this many actions were performed by the generator."
        )
        self.min_progression_spin = QtWidgets.QSpinBox()

        self.pre_place_label = QtWidgets.QLabel("Choose which items are pre-placed before generation occurs.")
        self.pre_place_artifact_check = QtWidgets.QCheckBox("Pre-place Artifacts")
        self.pre_place_phazon_check = QtWidgets.QCheckBox("Pre-place Phazon Suit")

    @property
    def game_specific_widgets(self) -> Iterable[QtWidgets.QWidget]:
        yield self.min_progression_label
        yield self.min_progression_spin
        yield self.pre_place_label
        yield self.pre_place_artifact_check
        yield self.pre_place_phazon_check

    @property
    def experimental_settings(self) -> Iterable[QtWidgets.QWidget]:
        yield from super().experimental_settings
        yield self.min_progression_label
        yield self.min_progression_spin
        yield self.pre_place_label
        yield self.pre_place_artifact_check
        yield self.pre_place_phazon_check

    def on_preset_changed(self, preset: Preset) -> None:
        assert isinstance(preset.configuration, PrimeConfiguration)
        super().on_preset_changed(preset)
        self.min_progression_spin.setValue(preset.configuration.artifact_minimum_progression)
        for f in _CHECKBOX_FIELDS:
            typing.cast("QtWidgets.QCheckBox", getattr(self, f"{f}_check")).setChecked(getattr(preset.configuration, f))
        self.min_progression_label.setEnabled(not self.pre_place_artifact_check.isChecked())
        self.min_progression_spin.setEnabled(not self.pre_place_artifact_check.isChecked())

    def _on_spin_changed(self) -> None:
        with self._editor as editor:
            editor.set_configuration_field(
                "artifact_minimum_progression",
                self.min_progression_spin.value(),
            )

    def _add_checkbox_persist_option(self, check: QtWidgets.QCheckBox, attribute_name: str) -> None:
        def persist(value: bool) -> None:
            with self._editor as editor:
                editor.set_configuration_field(attribute_name, value)

        signal_handling.on_checked(check, persist)
