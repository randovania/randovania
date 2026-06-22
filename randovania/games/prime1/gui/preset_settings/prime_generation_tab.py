from __future__ import annotations

import typing
from typing import TYPE_CHECKING

from PySide6 import QtWidgets

from randovania.games.prime1.layout.prime_configuration import PrimeConfiguration
from randovania.gui.lib import signal_handling
from randovania.gui.preset_settings.generation_tab import PresetGeneration
from randovania.gui.widgets import lines

if TYPE_CHECKING:
    from collections.abc import Iterable

    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset

_CHECKBOX_FIELDS = ["pre_place_artifact", "pre_place_phazon", "allow_underwater_movement_without_gravity"]


class PresetPrimeGeneration(PresetGeneration):
    min_progression_label: QtWidgets.QLabel
    min_progression_spin: QtWidgets.QSpinBox

    line1: QtWidgets.QFrame

    pre_place_label: QtWidgets.QLabel
    pre_place_artifact_check: QtWidgets.QCheckBox
    pre_place_phazon_check: QtWidgets.QCheckBox

    line2: QtWidgets.QFrame

    allow_underwater_movement_without_gravity_check: QtWidgets.QCheckBox
    allow_underwater_movement_without_gravity_label: QtWidgets.QLabel

    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)

        self.min_progression_spin.valueChanged.connect(self._on_spin_changed)
        for f in _CHECKBOX_FIELDS:
            self._add_checkbox_persist_option(getattr(self, f"{f}_check"), f)

        self.allow_underwater_movement_without_gravity_label.linkActivated.connect(
            self._on_click_link_resource_logic_details
        )

    def setupUi(self, obj: QtWidgets.QWidget) -> None:
        super().setupUi(obj)

        self.min_progression_label = QtWidgets.QLabel(
            "Only place artifacts after this many actions were performed by the generator."
        )
        self.min_progression_spin = QtWidgets.QSpinBox()

        self.line1 = lines.HLine()

        self.pre_place_label = QtWidgets.QLabel("Choose which items are pre-placed before generation occurs.")
        self.pre_place_artifact_check = QtWidgets.QCheckBox("Pre-place Artifacts")
        self.pre_place_phazon_check = QtWidgets.QCheckBox("Pre-place Phazon Suit")

        self.line2 = lines.HLine()

        self.allow_underwater_movement_without_gravity_check = QtWidgets.QCheckBox("Allow Dangerous Gravity Suit Logic")
        self.allow_underwater_movement_without_gravity_label = QtWidgets.QLabel(
            """
            <html><head/><body>
            <p> Allows the generator to require tricks which are only possible prior to Gravity Suit being obtained.</p>
            <p>
                <a href="resource-details://misc/NoGravity">
                <span style=" text-decoration: underline;">Click here</span></a>
                to see which rooms are affected.
            </p>
            <p>
                Enabling this option adds these alternatives to logic.
                To prevent the creation of an uncompletable save file, it is advised that
                you not pick up Gravity Suit until these rooms are cleared.
            </p>
            <p>
                Requires enabling <em>Gravityless Underwater Movement</em> in the Trick Level tab to have any effect.
            </p>
            </body></html>
            """
        )

    @property
    def game_specific_widgets(self) -> Iterable[QtWidgets.QWidget]:
        yield self.min_progression_label
        yield self.min_progression_spin
        yield self.line1
        yield self.pre_place_label
        yield self.pre_place_artifact_check
        yield self.pre_place_phazon_check
        yield self.line2
        yield self.allow_underwater_movement_without_gravity_check
        yield self.allow_underwater_movement_without_gravity_label

    @property
    def experimental_settings(self) -> Iterable[QtWidgets.QWidget]:
        yield from super().experimental_settings
        yield self.min_progression_label
        yield self.min_progression_spin
        yield self.line1
        yield self.pre_place_label
        yield self.pre_place_artifact_check
        yield self.pre_place_phazon_check
        yield self.line2

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
