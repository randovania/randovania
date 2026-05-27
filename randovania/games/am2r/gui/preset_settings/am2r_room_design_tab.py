from __future__ import annotations

import typing

from randovania.games.am2r.gui.generated.preset_am2r_room_design_ui import Ui_PresetAM2RRoomDesign
from randovania.games.am2r.layout import AM2RConfiguration
from randovania.gui.lib import signal_handling
from randovania.gui.preset_settings.preset_tab import PresetTab

if typing.TYPE_CHECKING:
    from PySide6 import QtWidgets

    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


class PresetAM2RRoomDesign(PresetTab, Ui_PresetAM2RRoomDesign):
    _CHECKBOX_FIELDS = [
        "septogg_helpers",
        "respawn_bomb_blocks",
        "grave_grotto_blocks",
        "nest_pipes",
        "softlock_prevention_blocks",
        "a3_entrance_blocks",
        "screw_blocks",
    ]

    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        self.setupUi(self)

        self.setCentralWidget(self.root_widget)

        # Signals
        for f in self._CHECKBOX_FIELDS:
            self._add_persist_option(getattr(self, f"{f}_check"), f)

    @classmethod
    def tab_title(cls) -> str:
        return "Room Changes"

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
        assert isinstance(config, AM2RConfiguration)
        for f in self._CHECKBOX_FIELDS:
            typing.cast("QtWidgets.QCheckBox", getattr(self, f"{f}_check")).setChecked(getattr(config, f))
