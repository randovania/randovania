from __future__ import annotations

import typing

from PySide6 import QtWidgets

from randovania.games.am2r.gui.generated.preset_am2r_patches_ui import Ui_PresetAM2RPatches
from randovania.games.am2r.layout import AM2RConfiguration
from randovania.gui.lib import signal_handling
from randovania.gui.preset_settings.preset_tab import PresetTab

if typing.TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset

_FIELDS = [
    "septogg_helpers",
    "respawn_bomb_blocks",
    "skip_cutscenes",
    "skip_save_cutscene",
    "skip_item_cutscenes",
    "grave_grotto_blocks",
    "fusion_mode",
    "supers_on_missile_doors",
    "nest_pipes",
    "softlock_prevention_blocks",
    "a3_entrance_blocks",
    "screw_blocks",
    "blue_save_doors",
    "force_blue_labs",
]


class PresetAM2RPatches(PresetTab, Ui_PresetAM2RPatches):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        self.setupUi(self)

        self.setCentralWidget(self.root_widget)

        # Signals
        for f in _FIELDS:
            self._add_persist_option(getattr(self, f"{f}_check"), f)

    @classmethod
    def tab_title(cls) -> str:
        return "Other"

    @classmethod
    def uses_patches_tab(cls) -> bool:
        return True

    def _add_persist_option(self, check: QtWidgets.QCheckBox, attribute_name: str):
        def persist(value: bool):
            with self._editor as editor:
                editor.set_configuration_field(attribute_name, value)

        signal_handling.on_checked(check, persist)

    def on_preset_changed(self, preset: Preset):
        config = preset.configuration
        assert isinstance(config, AM2RConfiguration)
        for f in _FIELDS:
            typing.cast(QtWidgets.QCheckBox, getattr(self, f"{f}_check")).setChecked(getattr(config, f))
