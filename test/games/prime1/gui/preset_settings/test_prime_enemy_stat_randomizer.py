import dataclasses
import uuid

import pytest
from PySide6 import QtWidgets

from randovania.game_description import default_database
from randovania.games.prime1.gui.preset_settings.prime_enemy_stat_randomizer import PresetEnemyAttributeRandomizer
from randovania.interface_common.preset_editor import PresetEditor
from randovania.games.game import RandovaniaGame

@pytest.mark.parametrize("game", [RandovaniaGame.METROID_PRIME])

def test_on_preset_changed(skip_qtbot, preset_manager, game):
    #Setup
    base = preset_manager.default_preset_for_game(RandovaniaGame.METROID_PRIME).get_preset()
    preset = dataclasses.replace(base,
                                 uuid=uuid.UUID('b41fde84-1f57-4b79-8cd6-3e5a78077fa6'),
                                 base_preset_uuid=base.uuid)
    editor = PresetEditor(preset)
    window = PresetEnemyAttributeRandomizer(editor)

    # Run
    window.on_preset_changed(editor.create_custom_preset_with())

    
