from __future__ import annotations

import typing
from typing import TYPE_CHECKING

from PySide6 import QtWidgets

from randovania.games.prime1.layout.prime_configuration import PrimeConfiguration
from randovania.gui.lib import signal_handling
from randovania.gui.preset_settings.dock_rando_tab import PresetDockRando
from randovania.layout.base.dock_rando_configuration import DockRandoMode

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset

_CHECKBOX_FIELDS = ["blue_save_doors", "blast_shield_lockon"]


class PresetPrimeDockRando(PresetDockRando):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)

        self.changes_box = QtWidgets.QGroupBox()
        self.changes_box.setTitle("Door Changes")
        self.changes_layout = QtWidgets.QVBoxLayout(self.changes_box)

        extra_widgets: list[tuple[type[QtWidgets.QCheckBox | QtWidgets.QLabel], str, str]] = [
            (
                QtWidgets.QCheckBox,
                "blue_save_doors_check",
                "Unlock Save Station Doors",
            ),
            (
                QtWidgets.QLabel,
                "blue_save_doors_label",
                "Sets all Save Station doors to blue regardless of door randomization mode",
            ),
            (
                QtWidgets.QCheckBox,
                "blast_shield_lockon_check",
                "Enable Blast Shield Lock-On",
            ),
            (
                QtWidgets.QLabel,
                "blast_shield_lockon_label",
                "Makes all Blast Shield locks targetable in Combat Visor",
            ),
        ]

        # Add each widget
        for widget_type, attr_name, desc in extra_widgets:
            setattr(self, attr_name, widget_type())
            widget = getattr(self, attr_name)
            widget.setText(desc)
            if widget_type == QtWidgets.QLabel:
                assert isinstance(widget, QtWidgets.QLabel)
                widget.setWordWrap(True)

            self.changes_layout.addWidget(widget)

        # Add the group box
        self.scroll_area_layout.insertWidget(0, self.changes_box)

        # Checkbox Signals
        for f in _CHECKBOX_FIELDS:
            self._add_checkbox_persist_option(getattr(self, f"{f}_check"), f)

    def _on_mode_changed(self, value: DockRandoMode) -> None:
        super()._on_mode_changed(value)
        with self._editor as editor:
            assert isinstance(editor.configuration, PrimeConfiguration)
            if value == DockRandoMode.VANILLA:
                editor.set_configuration_field("blast_shield_lockon", False)
            else:
                editor.set_configuration_field("blue_save_doors", True)
                editor.set_configuration_field("blast_shield_lockon", True)

    def _add_checkbox_persist_option(self, check: QtWidgets.QCheckBox, attribute_name: str) -> None:
        def persist(value: bool) -> None:
            with self._editor as editor:
                editor.set_configuration_field(attribute_name, value)

        signal_handling.on_checked(check, persist)

    def on_preset_changed(self, preset: Preset) -> None:
        super().on_preset_changed(preset)
        config = preset.configuration
        assert isinstance(config, PrimeConfiguration)
        for f in _CHECKBOX_FIELDS:
            typing.cast("QtWidgets.QCheckBox", getattr(self, f"{f}_check")).setChecked(getattr(config, f))
