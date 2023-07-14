from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6 import QtWidgets

from randovania.games.cave_story.layout.cs_configuration import CSConfiguration
from randovania.gui.preset_settings.generation_tab import PresetGeneration

if TYPE_CHECKING:
    from collections.abc import Iterable

    from randovania.layout.preset import Preset


class PresetCSGeneration(PresetGeneration):
    def setupUi(self, obj):
        super().setupUi(obj)
        self._create_puppy_checkbox()

    @property
    def game_specific_widgets(self) -> Iterable[QtWidgets.QWidget]:
        yield self._puppy_widget

    def on_preset_changed(self, preset: Preset):
        assert isinstance(preset.configuration, CSConfiguration)
        super().on_preset_changed(preset)
        self._puppy_widget.setChecked(preset.configuration.puppies_anywhere)

    def _create_puppy_checkbox(self):
        puppy = QtWidgets.QCheckBox("Shuffle puppies anywhere")
        puppy.setToolTip(
            "When disabled, puppies will only be shuffled within the Sand Zone. "
            "When enabled, puppies can be placed in any valid location."
        )
        puppy.stateChanged.connect(self._on_puppy_changed)
        self._puppy_widget = puppy

    def _on_puppy_changed(self):
        anywhere = self._puppy_widget.isChecked()
        with self._editor as editor:
            editor.set_configuration_field("puppies_anywhere", anywhere)
