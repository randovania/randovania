from __future__ import annotations

import dataclasses
import uuid
from unittest.mock import MagicMock

import pytest
from PySide6 import QtCore

from randovania.game_description import default_database
from randovania.game_description.db.area_identifier import AreaIdentifier
from randovania.games.common.prime_family.gui.elevators_tab import PresetElevators
from randovania.games.game import RandovaniaGame
from randovania.games.prime1.layout import prime_configuration
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.lib.teleporters import TeleporterShuffleMode, TeleporterTargetList


@pytest.mark.parametrize("game", [RandovaniaGame.METROID_PRIME, RandovaniaGame.METROID_PRIME_ECHOES])
def test_on_preset_changed(skip_qtbot, preset_manager, game):
    # Setup
    base = preset_manager.default_preset_for_game(game).get_preset()
    preset = dataclasses.replace(base, uuid=uuid.UUID('b41fde84-1f57-4b79-8cd6-3e5a78077fa6'))
    options = MagicMock()
    editor = PresetEditor(preset, options)
    window = PresetElevators(editor, default_database.game_description_for(preset.game), MagicMock())

    # Run
    window.on_preset_changed(editor.create_custom_preset_with())

    # Assert
    num_areas = len(TeleporterTargetList.nodes_list(preset.game))
    assert len(window._elevator_target_for_area) == num_areas


def test_check_credits(skip_qtbot, preset_manager):
    # Setup
    game = RandovaniaGame.METROID_PRIME
    base = preset_manager.default_preset_for_game(game).get_preset()
    assert isinstance(base.configuration, prime_configuration.PrimeConfiguration)
    preset = dataclasses.replace(
        base,
        uuid=uuid.UUID('b41fde84-1f57-4b79-8cd6-3e5a78077fa6'),
        configuration=dataclasses.replace(
            base.configuration,
            elevators=dataclasses.replace(
                base.configuration.elevators,
                mode=TeleporterShuffleMode.ONE_WAY_ANYTHING,
            ),
        )
    )
    options = MagicMock()
    editor = PresetEditor(preset, options)
    window = PresetElevators(editor, default_database.game_description_for(preset.game), MagicMock())
    window.on_preset_changed(editor.create_custom_preset_with())

    # Run
    skip_qtbot.mouseClick(
        window._elevator_target_for_area[AreaIdentifier("End of Game", "Credits")],
        QtCore.Qt.MouseButton.LeftButton,
    )
