from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from randovania.games.prime3.gui.generated.preset_teleporters_prime3_ui import (
    Ui_PresetTeleportersPrime3,
)
from randovania.games.prime3.layout.corruption_configuration import CorruptionConfiguration
from randovania.gui.lib import signal_handling
from randovania.gui.lib.node_list_helper import NodeListHelper
from randovania.gui.preset_settings.preset_teleporter_tab import PresetTeleporterTab
from randovania.layout.lib.teleporters import (
    TeleporterShuffleMode,
)

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.games.common.prime_family.layout.lib.prime_trilogy_teleporters import (
        PrimeTrilogyTeleporterConfiguration,
    )
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


class PresetTeleportersPrime3(PresetTeleporterTab, Ui_PresetTeleportersPrime3, NodeListHelper):
    teleporter_mode_to_description = {
        TeleporterShuffleMode.VANILLA: "All elevators are connected to where they do in the original game.",
    }

    def __init__(
        self,
        editor: PresetEditor,
        game_description: GameDescription,
        window_manager: WindowManager,
    ):
        super().__init__(editor, game_description, window_manager)
        signal_handling.on_checked(self.skip_final_bosses_check, self._update_require_final_bosses)

        # Keep the framework for teleporters for future use, but currently stubbed.
        self.teleporters_source_group.setVisible(False)
        self.teleporters_target_group.setVisible(False)
        self.teleporters_combo.setVisible(False)
        self.teleporters_description_label.setVisible(False)

    def setup_ui(self) -> None:
        self.setupUi(self)

    @classmethod
    def tab_title(cls) -> str:
        return "Connections"

    def _create_source_teleporters(self) -> None:
        pass

    def _update_require_final_bosses(self, checked: bool) -> None:
        with self._editor as editor:
            editor.layout_configuration_teleporters = dataclasses.replace(
                editor.layout_configuration_teleporters,
                skip_final_bosses=checked,
            )

    def on_preset_changed(self, preset: Preset) -> None:
        assert isinstance(preset.configuration, CorruptionConfiguration)
        config = preset.configuration
        config_teleporters: PrimeTrilogyTeleporterConfiguration = config.teleporters
        self.skip_final_bosses_check.setChecked(config_teleporters.skip_final_bosses)
