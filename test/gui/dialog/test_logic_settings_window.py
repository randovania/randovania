import dataclasses
import uuid

import pytest

from randovania.games.game import RandovaniaGame
from randovania.gui.preset_settings.logic_settings_window import LogicSettingsWindow
from randovania.interface_common.preset_editor import PresetEditor


@pytest.mark.parametrize("game", [RandovaniaGame.METROID_PRIME, RandovaniaGame.METROID_PRIME_ECHOES, RandovaniaGame.METROID_PRIME_CORRUPTION])
def test_on_preset_changed(skip_qtbot, preset_manager, game):
    # Setup
    base = preset_manager.default_preset_for_game(game).get_preset()
    preset = dataclasses.replace(base,
                                 uuid=uuid.UUID('b41fde84-1f57-4b79-8cd6-3e5a78077fa6'),
                                 base_preset_uuid=base.uuid)
    editor = PresetEditor(preset)
    window = LogicSettingsWindow(None, editor)

    # Run
    window.on_preset_changed(editor.create_custom_preset_with())
