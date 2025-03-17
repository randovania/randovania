from __future__ import annotations

import typing

from randovania.games.samus_returns.gui.generated.preset_msr_patches_ui import Ui_PresetMSRPatches
from randovania.games.samus_returns.layout.msr_configuration import FinalBossConfiguration
from randovania.gui.lib import signal_handling
from randovania.gui.preset_settings.preset_tab import PresetTab

if typing.TYPE_CHECKING:
    from PySide6 import QtWidgets

    from randovania.game_description.game_description import GameDescription
    from randovania.games.samus_returns.layout import MSRConfiguration
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset

_FIELDS = [
    "elevator_grapple_blocks",
    "area3_interior_shortcut_no_grapple",
    "charge_door_buff",
    "beam_door_buff",
    "beam_burst_buff",
    "nerf_super_missiles",
    "surface_crumbles",
    "area1_crumbles",
    "reverse_area8",
]


class PresetMSRPatches(PresetTab, Ui_PresetMSRPatches):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        self.setupUi(self)

        # Signals
        for f in _FIELDS:
            self._add_persist_option(getattr(self, f"{f}_check"), f)

    @classmethod
    def tab_title(cls) -> str:
        return "Optional Patches"

    @classmethod
    def header_name(cls) -> str | None:
        return None

    def _add_persist_option(self, check: QtWidgets.QCheckBox, attribute_name: str) -> None:
        def persist(value: bool) -> None:
            with self._editor as editor:
                editor.set_configuration_field(attribute_name, value)

        signal_handling.on_checked(check, persist)

    def on_preset_changed(self, preset: Preset) -> None:
        config = typing.cast("MSRConfiguration", preset.configuration)

        if config.final_boss == FinalBossConfiguration.QUEEN:
            self.reverse_area8_check.setEnabled(False)

        for f in _FIELDS:
            typing.cast("QtWidgets.QCheckBox", getattr(self, f"{f}_check")).setChecked(getattr(config, f))
