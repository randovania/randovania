from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6 import QtWidgets

from randovania.games.yokus_island_express.layout import YokuConfiguration
from randovania.games.yokus_island_express.layout.yokus_island_express_configuration import MAXIMUM_STARTING_FRUIT
from randovania.gui.preset_settings.preset_tab import PresetTab

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


class PresetYokuPatches(PresetTab[YokuConfiguration]):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)

        self.root_widget = QtWidgets.QWidget(self)
        self.root_layout = QtWidgets.QVBoxLayout(self.root_widget)

        self.starting_fruit_layout = QtWidgets.QHBoxLayout()
        self.starting_fruit_label = QtWidgets.QLabel("Starting fruit", self.root_widget)
        self.starting_fruit_layout.addWidget(self.starting_fruit_label)
        self.starting_fruit_spin = QtWidgets.QSpinBox(self.root_widget)
        self.starting_fruit_spin.setRange(0, MAXIMUM_STARTING_FRUIT)
        self.starting_fruit_layout.addWidget(self.starting_fruit_spin)
        self.root_layout.addLayout(self.starting_fruit_layout)

        self.starting_fruit_description = QtWidgets.QLabel(self.root_widget)
        self.starting_fruit_description.setWordWrap(True)
        self.starting_fruit_description.setText(
            "The fruit you start with. The wallet holds 100 fruit, plus 50 for each Wallet Upgrade."
        )
        self.root_layout.addWidget(self.starting_fruit_description)
        self.root_layout.addStretch()

        self.setCentralWidget(self.root_widget)

        self.starting_fruit_spin.valueChanged.connect(self._on_starting_fruit_changed)

    @classmethod
    def tab_title(cls) -> str:
        return "Other"

    @classmethod
    def header_name(cls) -> str | None:
        return cls.GAME_MODIFICATIONS_HEADER

    def _on_starting_fruit_changed(self, value: int) -> None:
        with self._editor as editor:
            editor.set_configuration_field("starting_fruit", value)

    def on_preset_changed(self, preset: Preset[YokuConfiguration]) -> None:
        self.starting_fruit_spin.blockSignals(True)
        self.starting_fruit_spin.setValue(preset.configuration.starting_fruit)
        self.starting_fruit_spin.blockSignals(False)
