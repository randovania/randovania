from __future__ import annotations

import typing

from PySide6 import QtWidgets

from randovania.games.samus_returns.layout import MSRConfiguration
from randovania.gui.generated.preset_msr_patches_ui import Ui_PresetMSRPatches
from randovania.gui.preset_settings.preset_tab import PresetTab

if typing.TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset

_FIELDS = [
    "elevator_grapple_blocks",
    "area3_interior_shortcut_no_grapple",
    "nerf_power_bombs",
    "nerf_super_missiles",
    "surface_crumbles",
    "area1_crumbles",
]


class PresetMSRPatches(PresetTab, Ui_PresetMSRPatches):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        self.setupUi(self)

        self.setCentralWidget(self.root_widget)

    @classmethod
    def tab_title(cls) -> str:
        return "Optional Patches"

    @classmethod
    def uses_patches_tab(cls) -> bool:
        return True

    def on_preset_changed(self, preset: Preset):
        config = typing.cast(MSRConfiguration, preset.configuration)

        for f in _FIELDS:
            typing.cast(QtWidgets.QCheckBox, getattr(self, f"{f}_check")).setChecked(getattr(config, f))
