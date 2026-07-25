from __future__ import annotations

import typing

from randovania.games.prime_hunters.gui.generated.preset_prime_hunters_gameplay_ui import Ui_PresetHuntersGameplay
from randovania.games.prime_hunters.layout.prime_hunters_configuration import HuntersConfiguration
from randovania.gui.lib import signal_handling
from randovania.gui.preset_settings.preset_tab import PresetTab

if typing.TYPE_CHECKING:
    from PySide6 import QtWidgets

    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


_FIELDS = [
    "skip_planet_intros",
]


class PresetHuntersGameplay(PresetTab[HuntersConfiguration], Ui_PresetHuntersGameplay):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        self.setupUi(self)

        self.energy_capacity_spin_box.valueChanged.connect(self._persist_capacity)

        # Signals
        for f in _FIELDS:
            self._add_persist_option(getattr(self, f"{f}_check"), f)

    @classmethod
    def tab_title(cls) -> str:
        return "Gameplay"

    @classmethod
    def header_name(cls) -> str | None:
        return None

    def on_preset_changed(self, preset: Preset[HuntersConfiguration]) -> None:
        config = preset.configuration

        self.energy_capacity_spin_box.setValue(config.starting_energy)

        for f in _FIELDS:
            typing.cast("QtWidgets.QCheckBox", getattr(self, f"{f}_check")).setChecked(getattr(config, f))

    def _persist_capacity(self) -> None:
        with self._editor as editor:
            editor.set_configuration_field("starting_energy", int(self.energy_capacity_spin_box.value()))

    def _add_persist_option(self, check: QtWidgets.QCheckBox, attribute_name: str) -> None:
        def persist(value: bool) -> None:
            with self._editor as editor:
                editor.set_configuration_field(attribute_name, value)

        signal_handling.on_checked(check, persist)
