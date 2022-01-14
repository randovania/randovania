import dataclasses
from typing import Iterable, Optional
from PySide2.QtWidgets import *
from randovania.games.game import RandovaniaGame
from randovania.gui.lib import common_qt_lib, signal_handling
from randovania.gui.preset_settings.preset_tab import PresetTab, PresetEditor
from randovania.gui.generated.preset_generation_ui import Ui_PresetGeneration
from randovania.layout.base.available_locations import RandomizationMode
from randovania.layout.base.damage_strictness import LayoutDamageStrictness
from randovania.layout.base.logical_resource_action import LayoutLogicalResourceAction
from randovania.layout.preset import Preset


# TODO: move to game classes (possibly in database?)
_GAME_SPECIFIC_MINIMAL_LOGIC_TEXT = {
    RandovaniaGame.METROID_PRIME: (
        "Items checked for: Morph Ball, Morph Ball Bomb, Wave Beam, Ice Beam, Phazon Suit, Artifacts."
    ),
    RandovaniaGame.METROID_PRIME_ECHOES: (
        "Items checked for: Dark Visor, Screw Attack, Torvus Keys, Sky Temple Keys."
    ),
    RandovaniaGame.METROID_PRIME_CORRUPTION: (
        "Items checked for: Nova Beam, X-Ray Visor, Hypermode, Grapple Lasso, Grapple Voltage, Hyper Grapple, Energy Cells."
    ),
}

class PresetGeneration(PresetTab, Ui_PresetGeneration):
    def __init__(self, editor: PresetEditor) -> None:
        super().__init__(editor)
        self.setupUi(self)

        # Game-specific Settings
        game_settings = self.game_specific_widgets
        if game_settings is not None:
            for w in game_settings:
                self.game_specific_layout.addWidget(w)
        else:
            self.game_specific_group.setVisible(False)

        # Item Placement
        signal_handling.on_checked(self.multi_pickup_placement_check, self._persist_multi_pickup_placement)
        signal_handling.on_checked(self.check_major_minor, self._persist_major_minor)
        signal_handling.on_checked(self.check_full_clear, self._persist_full_clear)

        # Logic Settings
        self.dangerous_combo.setItemData(0, LayoutLogicalResourceAction.RANDOMLY)
        self.dangerous_combo.setItemData(1, LayoutLogicalResourceAction.LAST_RESORT)
        signal_handling.on_combo(self.dangerous_combo, self._on_dangerous_changed)

        signal_handling.on_checked(self.trick_level_minimal_logic_check, self._on_trick_level_minimal_logic_check)
        for w in [
            self.trick_level_minimal_logic_check,
            self.trick_level_minimal_logic_label,
            self.minimal_logic_line
        ]:
            w.setVisible(self.game_enum in _GAME_SPECIFIC_MINIMAL_LOGIC_TEXT)
        self.trick_level_minimal_logic_label.setText(
            self.trick_level_minimal_logic_label.text().format(
                game_specific_text=_GAME_SPECIFIC_MINIMAL_LOGIC_TEXT.get(self.game_enum, "Unknown text")
            )
        )

        # Damage strictness
        self.damage_strictness_combo.setItemData(0, LayoutDamageStrictness.STRICT)
        self.damage_strictness_combo.setItemData(1, LayoutDamageStrictness.MEDIUM)
        self.damage_strictness_combo.setItemData(2, LayoutDamageStrictness.LENIENT)
        self.damage_strictness_combo.currentIndexChanged.connect(self._on_update_damage_strictness)
    
    def on_preset_changed(self, preset: Preset):
        layout = preset.configuration

        self.multi_pickup_placement_check.setChecked(layout.multi_pickup_placement)
        self.check_major_minor.setChecked(layout.available_locations.randomization_mode == RandomizationMode.MAJOR_MINOR_SPLIT)
        self.check_full_clear.setChecked(layout.full_clear_generation)

        self.trick_level_minimal_logic_check.setChecked(layout.trick_level.minimal_logic)
        common_qt_lib.set_combo_with_value(self.dangerous_combo, layout.logical_resource_action)

        common_qt_lib.set_combo_with_value(self.damage_strictness_combo, preset.configuration.damage_strictness)
    
    @property
    def uses_patches_tab(self) -> bool:
        return False

    @property
    def game_enum(self) -> RandovaniaGame:
        return self._editor._game
    
    @property
    def game_specific_widgets(self) -> Optional[Iterable[QWidget]]:
        return None

    def _persist_multi_pickup_placement(self, value: bool):
        with self._editor as editor:
            editor.set_configuration_field("multi_pickup_placement", value)
    
    def _persist_major_minor(self, value: bool):
        mode = RandomizationMode.MAJOR_MINOR_SPLIT if value else RandomizationMode.FULL
        with self._editor as editor:
            editor.available_locations = dataclasses.replace(editor.available_locations, randomization_mode=mode)
    
    def _persist_full_clear(self, value: bool):
        with self._editor as editor:
            editor.set_configuration_field("full_clear_generation", value)
    
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
