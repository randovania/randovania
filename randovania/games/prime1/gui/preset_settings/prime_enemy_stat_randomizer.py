from PySide6 import QtWidgets

from randovania.gui.generated.preset_prime_enemy_stat_randomizer_ui import Ui_EnemyAttributeRandomizer
from randovania.gui.preset_settings.preset_tab import PresetTab
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.preset import Preset

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
        self.minimum_label.setEnabled(not Activate_Randomizer)
        self.maximum_label.setEnabled(not Activate_Randomizer)
        self.scale_attribute_label.setEnabled(not Activate_Randomizer)
        self.range_scale_low.setEnabled(not Activate_Randomizer)
        self.range_scale_high.setEnabled(not Activate_Randomizer)
        self.health_attribute_label.setEnabled(not Activate_Randomizer)
        self.range_health_low.setEnabled(not Activate_Randomizer)
        self.range_health_high.setEnabled(not Activate_Randomizer)
        self.speed_attribute_label.setEnabled(not Activate_Randomizer)
        self.range_speed_low.setEnabled(not Activate_Randomizer)
        self.range_speed_high.setEnabled(not Activate_Randomizer)
        self.damage_attribute_label.setEnabled(not Activate_Randomizer)
        self.range_damage_low.setEnabled(not Activate_Randomizer)
        self.range_damage_high.setEnabled(not Activate_Randomizer)
        self.knockback_attribute_label.setEnabled(not Activate_Randomizer)
        self.range_knockback_low.setEnabled(not Activate_Randomizer)
        self.range_knockback_high.setEnabled(not Activate_Randomizer)
        self.label.setEnabled(not Activate_Randomizer)
        self.label_2.setEnabled(not Activate_Randomizer)

    def on_preset_changed(self, preset: Preset):
        print(preset)
        config = preset.configuration
        if hasattr(config.enemy_attributes, 'enemy_rando_range_scale_low'):
            self.range_scale_low.setValue(config.enemy_attributes.enemy_rando_range_scale_low)
        else:
            setattr(config.enemy_attributes, 'enemy_rando_range_scale_low', None)
        if hasattr(config.enemy_attributes, 'enemy_rando_range_scale_high'):
            self.range_scale_high.setValue(config.enemy_attributes.enemy_rando_range_scale_high)
        else:
            setattr(config.enemy_attributes, 'enemy_rando_range_scale_high', None)
        if hasattr(config.enemy_attributes, 'enemy_rando_range_health_low'):
            self.range_health_low.setValue(config.enemy_attributes.enemy_rando_range_health_low)
        else:
            setattr(config.enemy_attributes, 'enemy_rando_range_health_low', None)
        if hasattr(config.enemy_attributes, 'enemy_rando_range_health_high'):
            self.range_health_high.setValue(config.enemy_attributes.enemy_rando_range_health_high)
        else:
            setattr(config.enemy_attributes, 'enemy_rando_range_health_high', None)
        if hasattr(config.enemy_attributes, 'enemy_rando_range_speed_low'):
            self.range_speed_low.setValue(config.enemy_attributes.enemy_rando_range_speed_low)
        else:
            setattr(config.enemy_attributes, 'enemy_rando_range_speed_low', None)
        if hasattr(config.enemy_attributes, 'enemy_rando_range_speed_high'):
            self.range_speed_high.setValue(config.enemy_attributes.enemy_rando_range_speed_high)
        else:
            setattr(config.enemy_attributes, 'enemy_rando_range_speed_high', None)
        if hasattr(config.enemy_attributes, 'enemy_rando_range_damage_low'):
            self.range_damage_low.setValue(config.enemy_attributes.enemy_rando_range_damage_low)
        else:
            setattr(config.enemy_attributes, 'enemy_rando_range_damage_low', None)
        if hasattr(config.enemy_attributes, 'enemy_rando_range_damage_high'):
            self.range_damage_high.setValue(config.enemy_attributes.enemy_rando_range_damage_high)
        else:
            setattr(config.enemy_attributes, 'enemy_rando_range_damage_high', None)
        if hasattr(config.enemy_attributes, 'enemy_rando_range_knockback_low'):
            self.range_knockback_low.setValue(config.enemy_attributes.enemy_rando_range_knockback_low)
        else:
            setattr(config.enemy_attributes, 'enemy_rando_range_knockback_low', None)
        if hasattr(config.enemy_attributes, 'enemy_rando_range_knockback_high'):
            self.range_knockback_high.setValue(config.enemy_attributes.enemy_rando_range_knockback_high)
        else:
            setattr(config.enemy_attributes, 'enemy_rando_range_knockback_high', None)
        if hasattr(config.enemy_attributes, 'enemy_rando_diff_xyz'):
            self.diff_xyz.setChecked(config.enemy_attributes.enemy_rando_diff_xyz)
        else:
            setattr(config.enemy_attributes, 'enemy_rando_diff_xyz', None)


    def _on_spin_changed_range_scale_low(self):
        with self._editor as editor:
            editor.set_configuration_field(
                "enemy_rando_range_scale_low",
                self.range_scale_low.value(),
            )

    def _on_spin_changed_range_scale_high(self):
        with self._editor as editor:
            editor.set_configuration_field(
                "enemy_rando_range_scale_high",
                self.range_scale_high.value(),
            )

    def _on_spin_changed_range_health_low(self):
        with self._editor as editor:
            editor.set_configuration_field(
                "enemy_rando_range_health_low",
                self.range_health_low.value(),
            )

    def _on_spin_changed_range_health_high(self):
        with self._editor as editor:
            editor.set_configuration_field(
                "enemy_rando_range_health_high",
                self.range_health_high.value(),
            )

    def _on_spin_changed_range_speed_low(self):
        with self._editor as editor:
            editor.set_configuration_field(
                "enemy_rando_range_speed_low",
                self.range_speed_low.value(),
            )

    def _on_spin_changed_range_speed_high(self):
        with self._editor as editor:
            editor.set_configuration_field(
                "enemy_rando_range_speed_high",
                self.range_speed_high.value(),
            )

    def _on_spin_changed_range_damage_low(self):
        with self._editor as editor:
            editor.set_configuration_field(
                "enemy_rando_range_damage_low",
                self.range_damage_low.value(),
            )

    def _on_spin_changed_range_damage_high(self):
        with self._editor as editor:
            editor.set_configuration_field(
                "enemy_rando_range_damage_high",
                self.range_damage_high.value(),
            )

    def _on_spin_changed_range_knockback_low(self):
        with self._editor as editor:
            editor.set_configuration_field(
                "enemy_rando_range_knockback_low",
                self.range_knockback_low.value(),
            )

    def _on_spin_changed_range_knockback_high(self):
        with self._editor as editor:
            editor.set_configuration_field(
                "enemy_rando_range_knockback_high",
                self.range_knockback_high.value(),
            )    

    def _on_check_change(self):
        with self._editor as editor:
            editor.set_configuration_field(
                "enemy_rando_diff_xyz",
                self.diff_xyz.isChecked(),
            )    
