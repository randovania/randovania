from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6 import QtWidgets

from randovania.games.prime1.layout.prime_configuration import PrimeConfiguration
from randovania.gui.preset_settings.generation_tab import PresetGeneration

if TYPE_CHECKING:
    from collections.abc import Iterable

    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


class PresetPrimeGeneration(PresetGeneration):
    min_progression_label: QtWidgets.QLabel
    min_progression_spin: QtWidgets.QSpinBox

    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)

        self.min_progression_spin.valueChanged.connect(self._on_spin_changed)

    def setupUi(self, obj):
        super().setupUi(obj)

        self.min_progression_label = QtWidgets.QLabel(
            "Only place artifacts after this many actions were performed by the generator."
        )
        self.min_progression_spin = QtWidgets.QSpinBox()

    @property
    def game_specific_widgets(self) -> Iterable[QtWidgets.QWidget]:
        yield self.min_progression_label
        yield self.min_progression_spin

    @property
    def experimental_settings(self) -> Iterable[QtWidgets.QWidget]:
        yield from super().experimental_settings
        yield self.min_progression_label
        yield self.min_progression_spin

    def on_preset_changed(self, preset: Preset):
        assert isinstance(preset.configuration, PrimeConfiguration)
        super().on_preset_changed(preset)
        self.min_progression_spin.setValue(preset.configuration.artifact_minimum_progression)

    def _on_spin_changed(self):
        with self._editor as editor:
            editor.set_configuration_field(
                "artifact_minimum_progression",
                self.min_progression_spin.value(),
            )
