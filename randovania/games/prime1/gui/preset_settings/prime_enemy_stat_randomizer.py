from PySide6 import QtWidgets
import dataclasses

from randovania.game_description.game_description import GameDescription
from randovania.gui.lib.window_manager import WindowManager
from randovania.gui.generated.preset_prime_enemy_stat_randomizer_ui import Ui_EnemyAttributeRandomizer
from randovania.gui.preset_settings.preset_tab import PresetTab
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.preset import Preset
from randovania.games.prime1.layout.prime_configuration import EnemyAttributeRandomizer

class PresetEnemyAttributeRandomizer(PresetTab, Ui_EnemyAttributeRandomizer):
    def __init__(self, editor: PresetEditor, game_description: GameDescription, window_manager: WindowManager):
        super().__init__(editor, game_description, window_manager)
        self.setupUi(self)

        self.enemy_stat_randomizer_description.setText(self.enemy_stat_randomizer_description.text().replace("color:#0000ff;", ""))

        # Signals
        self.activate_randomizer.stateChanged.connect(self._on_activation)
        self.range_scale_low.valueChanged.connect(self._on_spin_changed_range_scale_low)
        self.range_scale_high.valueChanged.connect(self._on_spin_changed_range_scale_high)
        self.range_health_low.valueChanged.connect(self._on_spin_changed_range_health_low)
        self.range_health_high.valueChanged.connect(self._on_spin_changed_range_health_high)
        self.range_speed_low.valueChanged.connect(self._on_spin_changed_range_speed_low)
        self.range_speed_high.valueChanged.connect(self._on_spin_changed_range_speed_high)
        self.range_damage_low.valueChanged.connect(self._on_spin_changed_range_damage_low)
        self.range_damage_high.valueChanged.connect(self._on_spin_changed_range_damage_high)
        self.range_knockback_low.valueChanged.connect(self._on_spin_changed_range_knockback_low)
        self.range_knockback_high.valueChanged.connect(self._on_spin_changed_range_knockback_high)
        self.diff_xyz.toggled.connect(self._on_diff_xyz_check_change)

    @classmethod
    def tab_title(cls) -> str:
        return "Enemy Attributes"

    @classmethod
    def uses_patches_tab(cls) -> bool:
        return True

    def _on_activation(self):
        checked: bool = self.activate_randomizer.isChecked()
        widget_arr = [self.minimum_label, self.maximum_label, self.scale_attribute_label, self.range_scale_low, self.range_scale_high, self.health_attribute_label,
                      self.range_health_low, self.range_health_high, self.speed_attribute_label, self.range_speed_low, self.range_speed_high, self.damage_attribute_label,
                      self.range_damage_low, self.range_damage_high, self.knockback_attribute_label, self.range_knockback_low, self.range_knockback_high, self.diff_xyz,
                      self.label, self.label_2]
        with self._editor as editor:
            if checked:
                editor.set_configuration_field("enemy_attributes", EnemyAttributeRandomizer(self.range_scale_low.value(), self.range_scale_high.value(),
                                                                                            self.range_health_low.value(), self.range_health_high.value(),
                                                                                            self.range_speed_low.value(), self.range_speed_high.value(),
                                                                                            self.range_damage_low.value(), self.range_damage_high.value(),
                                                                                            self.range_knockback_low.value(), self.range_knockback_high.value(),
                                                                                            self.diff_xyz.isChecked()))
            else:
                editor.set_configuration_field("enemy_attributes", None)
        for e in widget_arr:
            e.setEnabled(checked)

    def on_preset_changed(self, preset: Preset):
        config = preset.configuration
        if config.enemy_attributes is not None:
            self.activate_randomizer.setChecked(True)
            self.range_scale_low.setValue(config.enemy_attributes.enemy_rando_range_scale_low)
            self.range_scale_high.setValue(config.enemy_attributes.enemy_rando_range_scale_high)
            self.range_health_low.setValue(config.enemy_attributes.enemy_rando_range_health_low)
            self.range_health_high.setValue(config.enemy_attributes.enemy_rando_range_health_high)
            self.range_speed_low.setValue(config.enemy_attributes.enemy_rando_range_speed_low)
            self.range_speed_high.setValue(config.enemy_attributes.enemy_rando_range_speed_high)
            self.range_damage_low.setValue(config.enemy_attributes.enemy_rando_range_damage_low)
            self.range_damage_high.setValue(config.enemy_attributes.enemy_rando_range_damage_high)
            self.range_knockback_low.setValue(config.enemy_attributes.enemy_rando_range_knockback_low)
            self.range_knockback_high.setValue(config.enemy_attributes.enemy_rando_range_knockback_high)
            self.diff_xyz.setChecked(config.enemy_attributes.enemy_rando_diff_xyz)

    def _on_spin_changed_range_scale_low(self):
        config = self._editor.configuration.enemy_attributes
        config = dataclasses.replace(config, enemy_rando_range_scale_low=self.range_scale_low.value())
        self._set_enemy_attributes_in_editor(config)

    def _on_spin_changed_range_scale_high(self):
        config = self._editor.configuration.enemy_attributes
        config = dataclasses.replace(config, enemy_rando_range_scale_high=self.range_scale_high.value())
        self._set_enemy_attributes_in_editor(config)

    def _on_spin_changed_range_health_low(self):
        config = self._editor.configuration.enemy_attributes
        config = dataclasses.replace(config, enemy_rando_range_health_low=self.range_health_low.value())
        self._set_enemy_attributes_in_editor(config)

    def _on_spin_changed_range_health_high(self):
        config = self._editor.configuration.enemy_attributes
        config = dataclasses.replace(config, enemy_rando_range_health_high=self.range_health_high.value())
        self._set_enemy_attributes_in_editor(config)

    def _on_spin_changed_range_speed_low(self):
        config = self._editor.configuration.enemy_attributes
        config = dataclasses.replace(config, enemy_rando_range_speed_low=self.range_speed_low.value())
        self._set_enemy_attributes_in_editor(config)

    def _on_spin_changed_range_speed_high(self):
        config = self._editor.configuration.enemy_attributes
        config = dataclasses.replace(config, enemy_rando_range_speed_high=self.range_speed_high.value())
        self._set_enemy_attributes_in_editor(config)

    def _on_spin_changed_range_damage_low(self):
        config = self._editor.configuration.enemy_attributes
        config = dataclasses.replace(config, enemy_rando_range_damage_low=self.range_damage_low.value())
        self._set_enemy_attributes_in_editor(config)

    def _on_spin_changed_range_damage_high(self):
        config = self._editor.configuration.enemy_attributes
        config = dataclasses.replace(config, enemy_rando_range_damage_high=self.range_damage_high.value())
        self._set_enemy_attributes_in_editor(config)

    def _on_spin_changed_range_knockback_low(self):
        config = self._editor.configuration.enemy_attributes
        config = dataclasses.replace(config, enemy_rando_range_knockback_low=self.range_knockback_low.value())
        self._set_enemy_attributes_in_editor(config)

    def _on_spin_changed_range_knockback_high(self):
        config = self._editor.configuration.enemy_attributes
        config = dataclasses.replace(config, enemy_rando_range_knockback_high=self.range_knockback_high.value())
        self._set_enemy_attributes_in_editor(config)

    def _on_diff_xyz_check_change(self):
        config = self._editor.configuration.enemy_attributes
        config = dataclasses.replace(config, enemy_rando_diff_xyz=self.diff_xyz.isChecked())
        self._set_enemy_attributes_in_editor(config)

    def _set_enemy_attributes_in_editor(self, config):
        with self._editor as editor:
            editor.set_configuration_field(
                "enemy_attributes",
                config,
            )    
