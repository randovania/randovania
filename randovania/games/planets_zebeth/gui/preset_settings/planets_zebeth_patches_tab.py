from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.planets_zebeth.gui.generated.preset_planets_zebeth_patches_ui import Ui_PresetPlanetsZebethPatches
from randovania.games.planets_zebeth.layout import PlanetsZebethConfiguration
from randovania.gui.preset_settings.preset_tab import PresetTab

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset

# TODO: add walljump patch


class PresetPlanetsZebethPatches(PresetTab, Ui_PresetPlanetsZebethPatches):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)

        self.setupUi(self)

        # Signals
        self.warp_to_start_check.stateChanged.connect(self._persist_option_then_notify("warp_to_start"))
        self.open_missile_doors_with_one_missile_check.stateChanged.connect(
            self._persist_option_then_notify("open_missile_doors_with_one_missile")
        )
        self.allow_downward_shots_check.stateChanged.connect(self._persist_option_then_notify("allow_downward_shots"))

    @classmethod
    def tab_title(cls) -> str:
        return "Other"

    @classmethod
    def header_name(cls) -> str | None:
        return None

    def on_preset_changed(self, preset: Preset) -> None:
        config = preset.configuration
        assert isinstance(config, PlanetsZebethConfiguration)
        self.warp_to_start_check.setChecked(config.warp_to_start)
        self.open_missile_doors_with_one_missile_check.setChecked(config.open_missile_doors_with_one_missile)
        self.allow_downward_shots_check.setChecked(config.allow_downward_shots)
