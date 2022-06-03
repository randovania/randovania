import dataclasses
import uuid
from unittest.mock import MagicMock

import pytest

from randovania.games.game import RandovaniaGame
from randovania.gui.preset_settings.customize_preset_dialog import CustomizePresetDialog
from randovania.interface_common.preset_editor import PresetEditor


def test_on_preset_changed(skip_qtbot, preset_manager, game_enum):
    # Setup
    window_manager = MagicMock()

    base = preset_manager.default_preset_for_game(game_enum).get_preset()
    preset = dataclasses.replace(base,
                                 uuid=uuid.UUID('b41fde84-1f57-4b79-8cd6-3e5a78077fa6'),
                                 base_preset_uuid=base.uuid)
    editor = PresetEditor(preset)
    window = CustomizePresetDialog(window_manager, editor)

    # Run
    window.on_preset_changed(editor.create_custom_preset_with())
