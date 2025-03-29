from __future__ import annotations

import dataclasses
import typing

from PySide6.QtWidgets import QCheckBox

from randovania.games.dread.gui.generated.preset_dread_lights_ui import Ui_PresetDreadLights
from randovania.games.dread.layout.dread_configuration import DreadConfiguration, DreadLightConfiguration
from randovania.gui.lib import signal_handling
from randovania.gui.preset_settings.preset_tab import PresetTab

if typing.TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.gui.lib.window_manager import WindowManager
    from randovania.interface_common.preset_editor import PresetEditor
    from randovania.layout.preset import Preset


class PresetDreadLights(PresetTab, Ui_PresetDreadLights):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        self.setupUi(self)

        self._regions = DreadLightConfiguration()

        for region in self._regions.as_json.keys():
            check_name = f"{region}_check"

            region_check = QCheckBox(region.capitalize(), self)
            region_check.setObjectName(check_name)

            setattr(self, check_name, region_check)
            self.lights_out_layout.addWidget(region_check)
            self._add_persist_option(region_check, region)

        self.enable_button.pressed.connect(self._enable_all)
        self.disable_button.pressed.connect(self._disable_all)

    @classmethod
    def tab_title(cls) -> str:
        return "Lights"

    @classmethod
    def header_name(cls) -> str | None:
        return None

    def _enable_all(self) -> None:
        for region in self._regions.as_json.keys():
            typing.cast("QCheckBox", getattr(self, f"{region}_check")).setChecked(True)

    def _disable_all(self) -> None:
        for region in self._regions.as_json.keys():
            typing.cast("QCheckBox", getattr(self, f"{region}_check")).setChecked(False)

    def _add_persist_option(self, check: QCheckBox, attribute_name: str) -> None:
        def persist(value: bool) -> None:
            with self._editor as editor:
                self._regions = dataclasses.replace(self._regions, **{attribute_name: value})
                editor.set_configuration_field("disabled_lights", self._regions)

        signal_handling.on_checked(check, persist)

    def on_preset_changed(self, preset: Preset) -> None:
        config = typing.cast("DreadConfiguration", preset.configuration)

        for region, is_checked in config.disabled_lights.as_json.items():
            typing.cast("QCheckBox", getattr(self, f"{region}_check")).setChecked(is_checked)
