from PySide6 import QtWidgets
import dataclasses

from randovania.gui.generated.preset_prime_enemy_stat_randomizer_ui import Ui_EnemyAttributeRandomizer
from randovania.gui.preset_settings.preset_tab import PresetTab
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.preset import Preset
from randovania.games.prime1.layout.prime_configuration import EnemyAttributeRandomizer

class PresetEnemyAttributeRandomizer(PresetTab, Ui_EnemyAttributeRandomizer):
    def __init__(self, editor: PresetEditor):
        super().__init__(editor)
        self.setupUi(self)

        self.enemy_stat_randomizer_description.setText(self.enemy_stat_randomizer_description.text().replace("color:#0000ff;", ""))

        # Signals
        self.Activate_Randomizer.stateChanged.connect(self._on_activation)
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
        self.diff_xyz.toggled.connect(self._on_check_change)

    @classmethod
    def tab_title(cls) -> str:
        return "Enemy Attributes"

    @classmethod
    def uses_patches_tab(cls) -> bool:
        return True

    def _on_activation(self):
        checked: bool = self.Activate_Randomizer.isChecked()
        with self._editor as editor:
            if checked:
                editor.set_configuration_field("enemy_attributes", EnemyAttributeRandomizer(1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, False))
                #print(EnemyAttributeRandomizer)
            else:
                editor.set_configuration_field("enemy_attributes", None)
        self.minimum_label.setEnabled(checked)
        self.maximum_label.setEnabled(checked)
        self.scale_attribute_label.setEnabled(checked)
        self.range_scale_low.setEnabled(checked)
        self.range_scale_high.setEnabled(checked)
        self.health_attribute_label.setEnabled(checked)
        self.range_health_low.setEnabled(checked)
        self.range_health_high.setEnabled(checked)
        self.speed_attribute_label.setEnabled(checked)
        self.range_speed_low.setEnabled(checked)
        self.range_speed_high.setEnabled(checked)
        self.damage_attribute_label.setEnabled(checked)
        self.range_damage_low.setEnabled(checked)
        self.range_damage_high.setEnabled(checked)
        self.knockback_attribute_label.setEnabled(checked)
        self.range_knockback_low.setEnabled(checked)
        self.range_knockback_high.setEnabled(checked)
        self.diff_xyz.setEnabled(checked)
        self.label.setEnabled(checked)
        self.label_2.setEnabled(checked)

    def on_preset_changed(self, preset: Preset):
        config = preset.configuration
        if config.enemy_attributes:
            with self._editor as editor:
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
        with self._editor as editor:
            config = editor.configuration.enemy_attributes
            config = dataclasses.replace(config, enemy_rando_range_scale_low=self.range_scale_low.value())
            editor.set_configuration_field(
                "enemy_attributes",
                config,
            )

    def _on_spin_changed_range_scale_high(self):
        with self._editor as editor:
            config = editor.configuration.enemy_attributes
            config = dataclasses.replace(config, enemy_rando_range_scale_high=self.range_scale_high.value())
            editor.set_configuration_field(
                "enemy_attributes",
                config,
            )

    def _on_spin_changed_range_health_low(self):
        with self._editor as editor:
            config = editor.configuration.enemy_attributes
            config = dataclasses.replace(config, enemy_rando_range_health_low=self.range_health_low.value())
            editor.set_configuration_field(
                "enemy_attributes",
                config,
            )

    def _on_spin_changed_range_health_high(self):
        with self._editor as editor:
            config = editor.configuration.enemy_attributes
            config = dataclasses.replace(config, enemy_rando_range_health_high=self.range_health_high.value())
            editor.set_configuration_field(
                "enemy_attributes",
                config,
            )

    def _on_spin_changed_range_speed_low(self):
        with self._editor as editor:
            config = editor.configuration.enemy_attributes
            config = dataclasses.replace(config, enemy_rando_range_speed_low=self.range_speed_low.value())
            editor.set_configuration_field(
                "enemy_attributes",
                config,
            )

    def _on_spin_changed_range_speed_high(self):
        with self._editor as editor:
            config = editor.configuration.enemy_attributes
            config = dataclasses.replace(config, enemy_rando_range_speed_high=self.range_speed_high.value())
            editor.set_configuration_field(
                "enemy_attributes",
                config,
            )

    def _on_spin_changed_range_damage_low(self):
        with self._editor as editor:
            config = editor.configuration.enemy_attributes
            config = dataclasses.replace(config, enemy_rando_range_damage_low=self.range_damage_low.value())
            editor.set_configuration_field(
                "enemy_attributes",
                config,
            )

    def _on_spin_changed_range_damage_high(self):
        with self._editor as editor:
            config = editor.configuration.enemy_attributes
            config = dataclasses.replace(config, enemy_rando_range_damage_high=self.range_damage_high.value())
            editor.set_configuration_field(
                "enemy_attributes",
                config,
            )

    def _on_spin_changed_range_knockback_low(self):
        with self._editor as editor:
            config = editor.configuration.enemy_attributes
            config = dataclasses.replace(config, enemy_rando_range_knockback_low=self.range_knockback_low.value())
            editor.set_configuration_field(
                "enemy_attributes",
                config,
            )

    def _on_spin_changed_range_knockback_high(self):
        with self._editor as editor:
            config = editor.configuration.enemy_attributes
            config = dataclasses.replace(config, enemy_rando_range_knockback_high=self.range_knockback_high.value())
            editor.set_configuration_field(
                "enemy_attributes",
                config,
            )    

    def _on_check_change(self):
        with self._editor as editor:
            config = editor.configuration.enemy_attributes
            config = dataclasses.replace(config, enemy_rando_diff_xyz=self.diff_xyz.isChecked())
            editor.set_configuration_field(
                "enemy_attributes",
                config,
            )    
