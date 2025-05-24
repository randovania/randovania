from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from PySide6 import QtCore

from randovania.games.prime_hunters.gui.generated.preset_prime_hunters_goal_ui import Ui_PresetHuntersGoal
from randovania.games.prime_hunters.layout.prime_hunters_configuration import (
    HuntersConfiguration,
    HuntersOctolithConfig,
)
from randovania.gui.preset_settings.preset_tab import PresetTab

if TYPE_CHECKING:
    from collections.abc import Callable

    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


class PresetHuntersGoal(PresetTab, Ui_PresetHuntersGoal):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        self.setupUi(self)

        self.goal_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        self.placed_slider.valueChanged.connect(self._on_placed_slider_changed)
        self._on_prefer_bosses(True)

    @classmethod
    def tab_title(cls) -> str:
        return "Goal"

    @classmethod
    def header_name(cls) -> str | None:
        return None

    def _edit_config(self, call: Callable[[HuntersOctolithConfig], HuntersOctolithConfig]) -> None:
        config = self._editor.configuration
        assert isinstance(config, HuntersConfiguration)

        with self._editor as editor:
            editor.set_configuration_field("octoliths", call(config.octoliths))

    def _on_prefer_bosses(self, value: bool) -> None:
        def edit(config: HuntersOctolithConfig) -> HuntersOctolithConfig:
            return dataclasses.replace(config, prefer_bosses=value)

        self._edit_config(edit)

    def _on_placed_slider_changed(self) -> None:
        self.placed_slider_label.setText(f"{self.placed_slider.value()}")

        def edit(config: HuntersOctolithConfig) -> HuntersOctolithConfig:
            return dataclasses.replace(config, placed_octoliths=self.placed_slider.value())

        self._edit_config(edit)

    def on_preset_changed(self, preset: Preset) -> None:
        assert isinstance(preset.configuration, HuntersConfiguration)
        octoliths = preset.configuration.octoliths
        self.placed_slider.setValue(octoliths.placed_octoliths)
