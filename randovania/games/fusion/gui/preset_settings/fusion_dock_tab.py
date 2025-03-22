from __future__ import annotations

import typing
from typing import TYPE_CHECKING

from PySide6 import QtWidgets

from randovania.games.fusion.layout.fusion_configuration import FusionConfiguration
from randovania.gui.lib import signal_handling
from randovania.gui.preset_settings.dock_rando_tab import PresetDockRando

if TYPE_CHECKING:
    from collections.abc import Iterator

    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset

_CHECKBOX_FIELDS = ["open_save_recharge_hatches", "unlock_sector_hub"]


class PresetFusionDocks(PresetDockRando):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager) -> None:
        super().__init__(editor, game_description, window_manager)

        # Fusion specific stuff
        self.changes_box = QtWidgets.QGroupBox()
        self.changes_box.setTitle("Door Changes")
        self.changes_layout = QtWidgets.QVBoxLayout(self.changes_box)

        extra_widgets: list[tuple[type[QtWidgets.QCheckBox | QtWidgets.QLabel], str, str]] = [
            (QtWidgets.QCheckBox, "unlock_sector_hub_check", "Unlock hatches in Sector Hub"),
            (
                QtWidgets.QLabel,
                "unlock_sector_hub_label",
                (
                    "Ensures all doors in the Sector Hub are open hatches, "
                    "giving access to the sector elevators at all times."
                ),
            ),
            (QtWidgets.QCheckBox, "open_save_recharge_hatches_check", "Unlock Save and Recharge Station Hatches"),
            (
                QtWidgets.QLabel,
                "open_save_recharge_hatches_label",
                "Ensures all Save and Recharge Station doors are open hatches, even with Door Lock Rando enabled.",
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

    @property
    def development_settings(self) -> Iterator[QtWidgets.QWidget]:
        # Hide the randomization settings unless running in preview mode
        yield self.settings_group

    def _add_checkbox_persist_option(self, check: QtWidgets.QCheckBox, attribute_name: str) -> None:
        def persist(value: bool) -> None:
            with self._editor as editor:
                editor.set_configuration_field(attribute_name, value)

        signal_handling.on_checked(check, persist)

    def on_preset_changed(self, preset: Preset) -> None:
        super().on_preset_changed(preset)
        config = preset.configuration
        assert isinstance(config, FusionConfiguration)
        for f in _CHECKBOX_FIELDS:
            typing.cast("QtWidgets.QCheckBox", getattr(self, f"{f}_check")).setChecked(getattr(config, f))
