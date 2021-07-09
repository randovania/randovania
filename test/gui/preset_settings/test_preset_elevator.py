import dataclasses
import uuid

import pytest

from randovania.game_description import default_database
from randovania.games.game import RandovaniaGame
from randovania.gui.preset_settings.elevators_tab import PresetElevators
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.lib.teleporters import TeleporterTargetList


@pytest.mark.parametrize("game", [RandovaniaGame.METROID_PRIME, RandovaniaGame.METROID_PRIME_ECHOES, RandovaniaGame.METROID_PRIME_CORRUPTION])
def test_on_preset_changed(skip_qtbot, preset_manager, game):
    # Setup
    base = preset_manager.default_preset_for_game(game).get_preset()
    preset = dataclasses.replace(base,
                                 uuid=uuid.UUID('b41fde84-1f57-4b79-8cd6-3e5a78077fa6'),
                                 base_preset_uuid=base.uuid)
    editor = PresetEditor(preset)
    window = PresetElevators(editor, default_database.game_description_for(preset.game))

    # Run
    window.on_preset_changed(editor.create_custom_preset_with())

    # Assert
    num_areas = len(TeleporterTargetList.areas_list(preset.game))
    assert len(window._elevator_target_for_area) == num_areas
    assert window.tab_title == "Teleporters" if preset.game == RandovaniaGame.METROID_PRIME_CORRUPTION else "Elevators"
