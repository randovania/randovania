from __future__ import annotations

import dataclasses
import uuid
from unittest.mock import MagicMock

import pytest
from PySide6 import QtCore

from randovania.game_description import default_database
from randovania.game_description.db.area_identifier import AreaIdentifier
from randovania.games.dread.gui.preset_settings.dread_teleporters_tab import PresetTeleportersDread
from randovania.games.game import RandovaniaGame
from randovania.games.prime1.gui.preset_settings.prime_teleporters_tab import PresetTeleportersPrime1
from randovania.games.prime1.layout import prime_configuration
from randovania.games.prime2.gui.preset_settings.echoes_teleporters_tab import PresetTeleportersPrime2
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.lib.teleporters import TeleporterShuffleMode, TeleporterTargetList


@pytest.mark.parametrize(
    "game", [RandovaniaGame.METROID_PRIME, RandovaniaGame.METROID_PRIME_ECHOES, RandovaniaGame.METROID_DREAD]
)
def test_on_preset_changed(skip_qtbot, preset_manager, game):
    # Setup
    base = preset_manager.default_preset_for_game(game).get_preset()
    preset = dataclasses.replace(base, uuid=uuid.UUID("b41fde84-1f57-4b79-8cd6-3e5a78077fa6"))
    options = MagicMock()
    editor = PresetEditor(preset, options)
    if game == RandovaniaGame.METROID_PRIME:
        window = PresetTeleportersPrime1(editor, default_database.game_description_for(preset.game), MagicMock())
    elif game == RandovaniaGame.METROID_PRIME_ECHOES:
        window = PresetTeleportersPrime2(editor, default_database.game_description_for(preset.game), MagicMock())
    else:
        window = PresetTeleportersDread(editor, default_database.game_description_for(preset.game), MagicMock())
    # Run
    window.on_preset_changed(editor.create_custom_preset_with())

    # Assert
    num_areas = len(TeleporterTargetList.nodes_list(preset.game))
    assert len(window._teleporters_target_for_area) == num_areas


def test_check_credits(skip_qtbot, preset_manager):
    # Setup
    game = RandovaniaGame.METROID_PRIME
    base = preset_manager.default_preset_for_game(game).get_preset()
    assert isinstance(base.configuration, prime_configuration.PrimeConfiguration)
    preset = dataclasses.replace(
        base,
        uuid=uuid.UUID("b41fde84-1f57-4b79-8cd6-3e5a78077fa6"),
        configuration=dataclasses.replace(
            base.configuration,
            teleporters=dataclasses.replace(
                base.configuration.teleporters,
                mode=TeleporterShuffleMode.ONE_WAY_ANYTHING,
            ),
        ),
    )
    options = MagicMock()
    editor = PresetEditor(preset, options)
    window = PresetTeleportersPrime1(editor, default_database.game_description_for(preset.game), MagicMock())
    window.on_preset_changed(editor.create_custom_preset_with())

    # Run
    skip_qtbot.mouseClick(
        window._teleporters_target_for_area[AreaIdentifier("End of Game", "Credits")],
        QtCore.Qt.MouseButton.LeftButton,
    )
