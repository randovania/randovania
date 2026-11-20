from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6 import QtWidgets

from randovania.games.yokus_island_express.layout import YokuConfiguration
from randovania.games.yokus_island_express.layout.yokus_island_express_configuration import BEACON_COUNT
from randovania.gui.preset_settings.preset_tab import PresetTab

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


class PresetYokuGoal(PresetTab[YokuConfiguration]):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)

        self.root_widget = QtWidgets.QWidget(self)
        self.root_layout = QtWidgets.QVBoxLayout(self.root_widget)

        self.required_beacons_layout = QtWidgets.QHBoxLayout()
        self.required_beacons_label = QtWidgets.QLabel("Required beacons", self.root_widget)
        self.required_beacons_layout.addWidget(self.required_beacons_label)
        self.required_beacons_spin = QtWidgets.QSpinBox(self.root_widget)
        self.required_beacons_spin.setRange(0, BEACON_COUNT)
        self.required_beacons_layout.addWidget(self.required_beacons_spin)
        self.root_layout.addLayout(self.required_beacons_layout)

        self.required_beacons_description = QtWidgets.QLabel(self.root_widget)
        self.required_beacons_description.setWordWrap(True)
        self.required_beacons_description.setText(
            "Nim starts the ceremony that leads to the final boss only once this many beacons are lit."
            " Each beacon takes 10 Wickerlings."
        )
        self.root_layout.addWidget(self.required_beacons_description)
        self.root_layout.addStretch()

        self.setCentralWidget(self.root_widget)

        self.required_beacons_spin.valueChanged.connect(self._on_required_beacons_changed)

    @classmethod
    def tab_title(cls) -> str:
        return "Goal"

    @classmethod
    def header_name(cls) -> str | None:
        return None

    def _on_required_beacons_changed(self, value: int) -> None:
        with self._editor as editor:
            editor.set_configuration_field("required_beacons", value)

    def on_preset_changed(self, preset: Preset[YokuConfiguration]) -> None:
        self.required_beacons_spin.blockSignals(True)
        self.required_beacons_spin.setValue(preset.configuration.required_beacons)
        self.required_beacons_spin.blockSignals(False)
