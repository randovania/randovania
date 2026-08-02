from __future__ import annotations

import typing
from typing import TYPE_CHECKING

from randovania.games.prime_hunters.gui.generated.preset_prime_hunters_extra_locations_ui import (
    Ui_PresetHuntersExtraLocations,
)
from randovania.games.prime_hunters.layout import HuntersConfiguration
from randovania.gui.lib import signal_handling
from randovania.gui.preset_settings.preset_tab import PresetTab

if TYPE_CHECKING:
    from PySide6 import QtWidgets

    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


_FIELDS = [
    "shuffle_item_refills",
    "shuffle_shield_keys",
]


class PresetHuntersExtraLocations(PresetTab[HuntersConfiguration], Ui_PresetHuntersExtraLocations):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        self.setupUi(self)

        # Signals
        for f in _FIELDS:
            self._add_persist_option(getattr(self, f"{f}_check_box"), f)

    @classmethod
    def tab_title(cls) -> str:
        return "Extra Locations"

    @classmethod
    def header_name(cls) -> str | None:
        return None

    def _add_persist_option(self, check: QtWidgets.QCheckBox, attribute_name: str) -> None:
        def persist(value: bool) -> None:
            with self._editor as editor:
                editor.set_configuration_field(attribute_name, value)

        signal_handling.on_checked(check, persist)

    def on_preset_changed(self, preset: Preset[HuntersConfiguration]) -> None:
        config = preset.configuration

        for f in _FIELDS:
            typing.cast("QtWidgets.QCheckBox", getattr(self, f"{f}_check_box")).setChecked(getattr(config, f))
