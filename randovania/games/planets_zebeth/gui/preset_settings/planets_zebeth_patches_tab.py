from __future__ import annotations

import typing
from typing import TYPE_CHECKING

from PySide6 import QtWidgets

from randovania.games.planets_zebeth.layout import PlanetsZebethConfiguration
from randovania.gui.lib import signal_handling
from randovania.gui.preset_settings.preset_tab import PresetTab

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset

# TODO: add walljump, downward shooting and open missile doors with 1 missile patches
_FIELDS = ["include_extra_pickups"]


class PresetPlanetsZebethPatches(PresetTab):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)

        self.root_widget = QtWidgets.QWidget(self)
        self.root_layout = QtWidgets.QVBoxLayout(self.root_widget)

        self.include_extra_pickups_check = QtWidgets.QCheckBox(self.root_widget)
        self.include_extra_pickups_check.setEnabled(True)
        self.include_extra_pickups_check.setText("Include Extra Pickups")
        self.root_layout.addWidget(self.include_extra_pickups_check)

        self.setCentralWidget(self.root_widget)

        # Signals
        for f in _FIELDS:
            self._add_persist_option(getattr(self, f"{f}_check"), f)

    @classmethod
    def tab_title(cls) -> str:
        return "Other"

    @classmethod
    def header_name(cls) -> str | None:
        return None

    def _add_persist_option(self, check: QtWidgets.QCheckBox, attribute_name: str) -> None:
        def persist(value: bool) -> None:
            with self._editor as editor:
                editor.set_configuration_field(attribute_name, value)

        signal_handling.on_checked(check, persist)

    def on_preset_changed(self, preset: Preset) -> None:
        config = preset.configuration
        assert isinstance(config, PlanetsZebethConfiguration)
        for f in _FIELDS:
            typing.cast("QtWidgets.QCheckBox", getattr(self, f"{f}_check")).setChecked(getattr(config, f))
