import dataclasses
from typing import Iterable

from PySide6.QtWidgets import *

from randovania.game_description.game_description import GameDescription
from randovania.games.game import RandovaniaGame
from randovania.gui.generated.preset_generation_ui import Ui_PresetGeneration
from randovania.gui.lib import common_qt_lib, signal_handling
from randovania.gui.lib.window_manager import WindowManager
from randovania.gui.preset_settings.preset_tab import PresetTab
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.base.available_locations import RandomizationMode
from randovania.layout.base.damage_strictness import LayoutDamageStrictness
from randovania.layout.base.logical_resource_action import LayoutLogicalResourceAction
from randovania.layout.preset import Preset


class PresetGeneration(PresetTab, Ui_PresetGeneration):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        self.setupUi(self)

        # Game-specific Settings
        game_settings = self.game_specific_widgets
        if game_settings is not None:
            for w in game_settings:
                self.game_specific_layout.addWidget(w)
        else:
            self.game_specific_group.setVisible(False)

        # Item Placement
        signal_handling.on_checked(self.check_major_minor, self._persist_major_minor)
        signal_handling.on_checked(self.local_first_progression_check, self._persist_local_first_progression)

        # Logic Settings
        self.dangerous_combo.setItemData(0, LayoutLogicalResourceAction.RANDOMLY)
        self.dangerous_combo.setItemData(1, LayoutLogicalResourceAction.LAST_RESORT)
        signal_handling.on_combo(self.dangerous_combo, self._on_dangerous_changed)

        signal_handling.on_checked(self.trick_level_minimal_logic_check, self._on_trick_level_minimal_logic_check)

        #Minimal Logic
        for w in [
            self.trick_level_minimal_logic_check,
            self.trick_level_minimal_logic_label,
            self.minimal_logic_line
        ]:
            w.setVisible(game_description.minimal_logic is not None)
        if game_description.minimal_logic is not None:
            self.trick_level_minimal_logic_label.setText(
                self.trick_level_minimal_logic_label.text().format(
                    game_specific_text=game_description.minimal_logic.description
                )
            )

        # Damage strictness
        self.damage_strictness_combo.setItemData(0, LayoutDamageStrictness.STRICT)
        self.damage_strictness_combo.setItemData(1, LayoutDamageStrictness.MEDIUM)
        self.damage_strictness_combo.setItemData(2, LayoutDamageStrictness.LENIENT)
        self.damage_strictness_combo.currentIndexChanged.connect(self._on_update_damage_strictness)

    def on_preset_changed(self, preset: Preset):
        layout = preset.configuration

        self.local_first_progression_check.setChecked(layout.first_progression_must_be_local)
        self.check_major_minor.setChecked(
            layout.available_locations.randomization_mode == RandomizationMode.MAJOR_MINOR_SPLIT)

        self.trick_level_minimal_logic_check.setChecked(layout.trick_level.minimal_logic)
        common_qt_lib.set_combo_with_value(self.dangerous_combo, layout.logical_resource_action)

        common_qt_lib.set_combo_with_value(self.damage_strictness_combo, preset.configuration.damage_strictness)

    @classmethod
    def tab_title(cls) -> str:
        return "Generation"

    @classmethod
    def uses_patches_tab(cls) -> bool:
        return False

    @property
    def game_enum(self) -> RandovaniaGame:
        return self._editor._game

    @property
    def game_specific_widgets(self) -> Iterable[QWidget] | None:
        return None

    def _persist_major_minor(self, value: bool):
        mode = RandomizationMode.MAJOR_MINOR_SPLIT if value else RandomizationMode.FULL
        with self._editor as editor:
            editor.available_locations = dataclasses.replace(editor.available_locations, randomization_mode=mode)

    def _persist_local_first_progression(self, value: bool):
        with self._editor as editor:
            editor.set_configuration_field("first_progression_must_be_local", value)

    def _on_dangerous_changed(self, value: LayoutLogicalResourceAction):
        with self._editor as editor:
            editor.set_configuration_field("logical_resource_action", value)

    def _on_trick_level_minimal_logic_check(self, state: bool):
        with self._editor as options:
            options.set_configuration_field(
                "trick_level",
                dataclasses.replace(options.configuration.trick_level,
                                    minimal_logic=state)
            )

    def _on_update_damage_strictness(self, new_index: int):
        with self._editor as editor:
            editor.layout_configuration_damage_strictness = self.damage_strictness_combo.currentData()
