from __future__ import annotations

import typing
from typing import TYPE_CHECKING

from PySide6 import QtWidgets

from randovania.games.am2r.layout.am2r_configuration import AM2RConfiguration
from randovania.gui.lib import signal_handling
from randovania.gui.preset_settings.dock_rando_tab import PresetDockRando

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset

_CHECKBOX_FIELDS = ["blue_save_doors", "force_blue_labs", "supers_on_missile_doors"]


class PresetAM2RDoors(PresetDockRando):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager) -> None:
        super().__init__(editor, game_description, window_manager)

        # AM2R specific stuff
        self.changes_box = QtWidgets.QGroupBox()
        self.changes_box.setTitle("Door Changes")
        self.changes_layout = QtWidgets.QVBoxLayout(self.changes_box)

        extra_widgets: list[tuple[type[QtWidgets.QCheckBox | QtWidgets.QLabel], str, str]] = [
            (QtWidgets.QCheckBox, "blue_save_doors_check", "Unlock Save Station Doors"),
            (
                QtWidgets.QLabel,
                "blue_save_doors_label",
                "Ensures all Save Station doors are normal (blue) doors, even with door lock rando enabled.",
            ),
            (QtWidgets.QCheckBox, "force_blue_labs_check", "Unlock Genetics Laboratory Doors"),
            (
                QtWidgets.QLabel,
                "force_blue_labs_label",
                (
                    "Ensures that the doors in the later parts of Genetics Laboratory are normal (blue) doors, "
                    "even with door lock rando enabled.\nTo be more precise, "
                    'all rooms after "Hatchling Room Underside" will have their doors changed.'
                ),
            ),
            (QtWidgets.QCheckBox, "supers_on_missile_doors_check", "Open Missile Doors with Super Missiles"),
            (
                QtWidgets.QLabel,
                "supers_on_missile_doors_label",
                "Determines whether Super Missiles can be used to open Missile Doors.",
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

    def _add_checkbox_persist_option(self, check: QtWidgets.QCheckBox, attribute_name: str) -> None:
        def persist(value: bool) -> None:
            with self._editor as editor:
                editor.set_configuration_field(attribute_name, value)

        signal_handling.on_checked(check, persist)

    def on_preset_changed(self, preset: Preset) -> None:
        super().on_preset_changed(preset)
        config = preset.configuration
        assert isinstance(config, AM2RConfiguration)
        for f in _CHECKBOX_FIELDS:
            typing.cast("QtWidgets.QCheckBox", getattr(self, f"{f}_check")).setChecked(getattr(config, f))
