from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6 import QtWidgets
from PySide6.QtWidgets import QFrame

from randovania.games.prime2.layout.echoes_configuration import EchoesConfiguration
from randovania.gui.preset_settings.dock_rando_tab import PresetDockRando
from randovania.layout.base.dock_rando_configuration import DockRandoMode

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor


class PresetEchoesDockRando(PresetDockRando):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager) -> None:
        super().__init__(editor, game_description, window_manager)
        self.new_patcher_warning_label = QtWidgets.QLabel(self)
        self.new_patcher_warning_label.setText(
            "Door lock randomization requires the experimental setting "
            '"Enable New Patcher" to function. \nEnabling any of the randomization '
            "modes will also enable that setting if it is not already enabled."
        )
        self.new_patcher_warning_label.setWordWrap(True)
        self.settings_layout.insertWidget(0, self.new_patcher_warning_label)

        self.line_2 = QFrame(self.new_patcher_warning_label)
        self.line_2.setFrameShape(QFrame.Shape.HLine)
        self.line_2.setFrameShadow(QFrame.Shadow.Sunken)

        self.settings_layout.insertWidget(1, self.line_2)

    def _on_mode_changed(self, value: DockRandoMode) -> None:
        super()._on_mode_changed(value)
        if value != DockRandoMode.VANILLA:
            with self._editor as editor:
                assert isinstance(editor.configuration, EchoesConfiguration)
                editor.set_configuration_field("use_new_patcher", True)
