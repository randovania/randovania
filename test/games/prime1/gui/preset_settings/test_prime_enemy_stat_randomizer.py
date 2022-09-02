import dataclasses
import uuid
from unittest.mock import MagicMock

import pytest
from PySide6 import QtWidgets
from PySide6.QtCore import Qt

from randovania.game_description import default_database
from randovania.games.prime1.gui.preset_settings.prime_enemy_stat_randomizer import PresetEnemyAttributeRandomizer
from randovania.interface_common.preset_editor import PresetEditor
from randovania.games.game import RandovaniaGame

@pytest.mark.parametrize("use_enemy_attribute_randomizer", [False, True])
def test_on_preset_changed(skip_qtbot, preset_manager, use_enemy_attribute_randomizer):
    #Setup
    base = preset_manager.default_preset_for_game(RandovaniaGame.METROID_PRIME).get_preset()
    preset = dataclasses.replace(base, uuid=uuid.UUID('b41fde84-1f57-4b79-8cd6-3e5a78077fa6'))
    editor = PresetEditor(preset)
    window = PresetEnemyAttributeRandomizer(editor, default_database.game_description_for(preset.game), MagicMock())

    if use_enemy_attribute_randomizer:
        skip_qtbot.mouseClick(window.activate_randomizer, Qt.LeftButton)

        window.range_scale_low.setValue(1.2)
        window.range_scale_high.setValue(1.7)
    
        window.range_health_low.setValue(0.12)
        window.range_health_high.setValue(1.272)
    
        window.range_speed_low.setValue(3.292)
        window.range_speed_high.setValue(7.2)
    
        window.range_damage_low.setValue(9.2)
        window.range_damage_high.setValue(99.21)
    
        window.range_knockback_low.setValue(0.2)
        window.range_knockback_high.setValue(0.5147)

        skip_qtbot.mouseClick(window.diff_xyz, Qt.LeftButton)
    else:
        pass
    
    # Run
    window.on_preset_changed(editor.create_custom_preset_with())

    # Assert
    if use_enemy_attribute_randomizer:
        assert editor.configuration.enemy_attributes.enemy_rando_range_scale_low == window.range_scale_low.value()
        assert editor.configuration.enemy_attributes.enemy_rando_range_scale_high == window.range_scale_high.value()

        assert editor.configuration.enemy_attributes.enemy_rando_range_health_low == window.range_health_low.value()
        assert editor.configuration.enemy_attributes.enemy_rando_range_health_high == window.range_health_high.value()

        assert editor.configuration.enemy_attributes.enemy_rando_range_speed_low == window.range_speed_low.value()
        assert editor.configuration.enemy_attributes.enemy_rando_range_speed_high == window.range_speed_high.value()

        assert editor.configuration.enemy_attributes.enemy_rando_range_damage_low == window.range_damage_low.value()
        assert editor.configuration.enemy_attributes.enemy_rando_range_damage_high == window.range_damage_high.value()

        assert editor.configuration.enemy_attributes.enemy_rando_range_knockback_low == window.range_knockback_low.value()
        assert editor.configuration.enemy_attributes.enemy_rando_range_knockback_high == window.range_knockback_high.value()

        assert editor.configuration.enemy_attributes.enemy_rando_diff_xyz == window.diff_xyz.isChecked()
    else:
        assert editor.configuration.enemy_attributes == None
