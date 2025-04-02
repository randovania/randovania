from __future__ import annotations

import typing

from randovania.games.fusion.gui.generated.preset_fusion_patches_ui import Ui_PresetFusionPatches
from randovania.games.fusion.layout import FusionConfiguration
from randovania.gui.lib import signal_handling
from randovania.gui.preset_settings.preset_tab import PresetTab

if typing.TYPE_CHECKING:
    from PySide6 import QtWidgets

    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


_FIELDS = [
    "instant_transitions",
    "anti_softlock",
    "short_intro_text",
]


class PresetFusionPatches(PresetTab, Ui_PresetFusionPatches):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        self.setupUi(self)

        self.setCentralWidget(self.root_widget)

        # Signals
        for f in _FIELDS:
            self._add_persist_option(getattr(self, f"{f}_check"), f)
        self.etank_capacity_spin_box.valueChanged.connect(self._persist_tank_capacity)

    @classmethod
    def tab_title(cls) -> str:
        return "Gameplay"

    @classmethod
    def header_name(cls) -> str | None:
        return cls.GAME_MODIFICATIONS_HEADER

    def _add_persist_option(self, check: QtWidgets.QCheckBox, attribute_name: str) -> None:
        def persist(value: bool) -> None:
            with self._editor as editor:
                editor.set_configuration_field(attribute_name, value)

        signal_handling.on_checked(check, persist)

    def _persist_tank_capacity(self) -> None:
        with self._editor as editor:
            editor.set_configuration_field("energy_per_tank", int(self.etank_capacity_spin_box.value()))

    def on_preset_changed(self, preset: Preset) -> None:
        config = preset.configuration
        assert isinstance(config, FusionConfiguration)
        for f in _FIELDS:
            typing.cast("QtWidgets.QCheckBox", getattr(self, f"{f}_check")).setChecked(getattr(config, f))
        self.etank_capacity_spin_box.setValue(config.energy_per_tank)
