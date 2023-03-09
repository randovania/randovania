import dataclasses
import uuid
from unittest.mock import MagicMock

import pytest
from PySide6 import QtCore
from PySide6.QtCore import Qt

from randovania.game_description import default_database
from randovania.game_description.world.area_identifier import AreaIdentifier
from randovania.games.cave_story.gui.preset_settings.cs_starting_area_tab import PresetCSStartingArea
from randovania.games.game import RandovaniaGame
from randovania.gui.preset_settings.starting_area_tab import PresetMetroidStartingArea, PresetStartingArea
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.base.base_configuration import StartingLocationList


@pytest.mark.parametrize("game", [RandovaniaGame.METROID_PRIME, RandovaniaGame.METROID_PRIME_ECHOES,
                                  RandovaniaGame.METROID_PRIME_CORRUPTION])
def test_on_preset_changed(skip_qtbot, preset_manager, game):
    # Setup
    base = preset_manager.default_preset_for_game(game).get_preset()
    preset = dataclasses.replace(base, uuid=uuid.UUID('b41fde84-1f57-4b79-8cd6-3e5a78077fa6'))
    editor = PresetEditor(preset)
    window = PresetStartingArea(editor, default_database.game_description_for(preset.game), MagicMock())

    # Run
    window.on_preset_changed(editor.create_custom_preset_with())

    # Assert
    num_areas = len(StartingLocationList.areas_list(preset.game))
    assert len(window._starting_location_for_area) == num_areas


def test_starting_location_world_select(skip_qtbot, preset_manager):
    # Setup
    base = preset_manager.default_preset_for_game(RandovaniaGame.METROID_PRIME_ECHOES).get_preset()
    preset = dataclasses.replace(base, uuid=uuid.UUID('b41fde84-1f57-4b79-8cd6-3e5a78077fa6'))
    editor = PresetEditor(preset)
    window = PresetMetroidStartingArea(editor, default_database.game_description_for(preset.game), MagicMock())
    skip_qtbot.addWidget(window)

    # Run
    checkbox_list = window._starting_location_for_world
    window.on_preset_changed(editor.create_custom_preset_with())
    assert len(checkbox_list) == 10
    temple_grounds_checkbox = checkbox_list["Temple Grounds"]
    assert temple_grounds_checkbox.checkState() == Qt.PartiallyChecked
    skip_qtbot.mouseClick(temple_grounds_checkbox, Qt.LeftButton)
    assert temple_grounds_checkbox.checkState() == Qt.Checked
    assert len(editor.configuration.starting_location.locations) == 39
    skip_qtbot.mouseClick(temple_grounds_checkbox, Qt.LeftButton)
    assert temple_grounds_checkbox.checkState() == Qt.Unchecked
    assert len(editor.configuration.starting_location.locations) == 0
    skip_qtbot.mouseClick(temple_grounds_checkbox, Qt.LeftButton)
    window.on_preset_changed(editor.create_custom_preset_with())
    assert temple_grounds_checkbox.checkState() == Qt.Checked
    assert len(editor.configuration.starting_location.locations) == 39


@pytest.mark.parametrize("game_enum", RandovaniaGame)
def test_quick_fill_default(skip_qtbot, preset_manager, game_enum: RandovaniaGame):
    # Setup
    base = preset_manager.default_preset_for_game(game_enum).get_preset()
    preset = dataclasses.replace(base, uuid=uuid.UUID('b41fde84-1f57-4b79-8cd6-3e5a78077fa6'))
    editor = PresetEditor(preset)
    window = PresetStartingArea(editor, default_database.game_description_for(preset.game), MagicMock())
    skip_qtbot.addWidget(window)

    # Run
    skip_qtbot.mouseClick(window.starting_area_quick_fill_default, QtCore.Qt.LeftButton)

    # Assert
    assert editor.configuration.starting_location.locations == (window.game_description.starting_location,)


def test_quick_fill_cs_classic(skip_qtbot, preset_manager):
    # Setup
    base = preset_manager.default_preset_for_game(RandovaniaGame.CAVE_STORY).get_preset()
    preset = dataclasses.replace(base, uuid=uuid.UUID('b41fde84-1f57-4b79-8cd6-3e5a78077fa6'))
    editor = PresetEditor(preset)
    window = PresetCSStartingArea(editor, default_database.game_description_for(preset.game), MagicMock())
    skip_qtbot.addWidget(window)

    # Run
    skip_qtbot.mouseClick(window.starting_area_quick_fill_classic, QtCore.Qt.LeftButton)

    # Assert
    expected = {
        AreaIdentifier("Mimiga Village", "Start Point"),
        AreaIdentifier("Mimiga Village", "Arthur's House"),
        AreaIdentifier("Labyrinth", "Camp")
    }
    assert set(editor.configuration.starting_location.locations) == expected
