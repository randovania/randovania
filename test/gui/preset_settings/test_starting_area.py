import dataclasses
import uuid
from unittest.mock import MagicMock

import pytest
from PySide6 import QtCore
from PySide6.QtCore import Qt

from randovania.game_description import default_database
from randovania.game_description.world.node import GenericNode
from randovania.game_description.world.node_identifier import NodeIdentifier
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
    num_areas = len(StartingLocationList.nodes_list(preset.game))
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
        NodeIdentifier.create("Mimiga Village", "Start Point", "Room Spawn"),
        NodeIdentifier.create("Mimiga Village", "Arthur's House", "Room Spawn"),
        NodeIdentifier.create("Labyrinth", "Camp", "Room Spawn")
    }
    assert set(editor.configuration.starting_location.locations) == expected

def test_check_credits(skip_qtbot, preset_manager):
    # Setup
    base = preset_manager.default_preset_for_game(RandovaniaGame.METROID_PRIME).get_preset()
    preset = dataclasses.replace(base, uuid=uuid.UUID('b41fde84-1f57-4b79-8cd6-3e5a78077fa6'))
    editor = PresetEditor(preset)
    window = PresetMetroidStartingArea(editor, default_database.game_description_for(preset.game), MagicMock())
    skip_qtbot.addWidget(window)

    not_expected = NodeIdentifier.create("End of Game", "Credits", "Event - Credits")

    checkbox_list = window._starting_location_for_node
    assert checkbox_list.get(not_expected, None) == None

def test_area_with_multiple_nodes(skip_qtbot, preset_manager):
    # Setup
    base = preset_manager.default_preset_for_game(RandovaniaGame.BLANK).get_preset()
    preset = dataclasses.replace(base, uuid=uuid.UUID('b41fde84-1f57-4b79-8cd6-3e5a78077fa6'))
    editor = PresetEditor(preset)

    game_desc = default_database.game_description_for(preset.game)                     
    window = PresetStartingArea(editor, default_database.game_description_for(preset.game), MagicMock())
    skip_qtbot.addWidget(window)
    window.on_preset_changed(editor.create_custom_preset_with())

    world = game_desc.world_list.world_with_name("Intro")
    starting_area = world.area_by_name("Starting Area")
    blue_key_room = world.area_by_name("Blue Key Room")

    default_start_point = NodeIdentifier.create(world.name, starting_area.name, "Spawn Point")
    second_start_point = NodeIdentifier.create(world.name, starting_area.name, "Second Spawn Point")
    blue_key_start_point = NodeIdentifier.create(world.name, blue_key_room.name, "Spawn Point")
    checkbox_node_list = window._starting_location_for_node
    checkbox_area_list = window._starting_location_for_area
    checkbox_world_list = window._starting_location_for_world
    starting_area_box = checkbox_area_list.get(default_start_point.area_identifier)
    blue_key_room_box = checkbox_area_list.get(blue_key_start_point.area_identifier)
    intro_world_box = checkbox_world_list.get(world.name)

    # check default start location is set
    assert checkbox_node_list.get(default_start_point, None) != None
    assert checkbox_node_list.get(second_start_point, None) != None
    assert checkbox_node_list.get(blue_key_start_point, None) != None
    assert intro_world_box != None
    assert starting_area_box != None
    assert blue_key_room_box != None
    assert len(editor.configuration.starting_location.locations) == 1

    # test checkboxes
    assert intro_world_box.checkState() == QtCore.Qt.PartiallyChecked
    assert starting_area_box.checkState() == QtCore.Qt.PartiallyChecked
    assert blue_key_room_box.checkState() == QtCore.Qt.Unchecked

    # click "Test Start" and check states
    test_node_checkbox = checkbox_node_list[second_start_point]
    skip_qtbot.mouseClick(test_node_checkbox, Qt.LeftButton)
    window.on_preset_changed(editor.create_custom_preset_with())
    assert len(editor.configuration.starting_location.locations) == 2
    assert intro_world_box.checkState() == QtCore.Qt.PartiallyChecked
    assert starting_area_box.checkState() == QtCore.Qt.Checked
    assert blue_key_room_box.checkState() == QtCore.Qt.Unchecked

    # toggle the area button
    skip_qtbot.mouseClick(starting_area_box, Qt.LeftButton)
    window.on_preset_changed(editor.create_custom_preset_with())
    assert len(editor.configuration.starting_location.locations) == 0
    assert intro_world_box.checkState() == QtCore.Qt.Unchecked
    assert starting_area_box.checkState() == QtCore.Qt.Unchecked
    assert blue_key_room_box.checkState() == QtCore.Qt.Unchecked

    skip_qtbot.mouseClick(starting_area_box, Qt.LeftButton)
    window.on_preset_changed(editor.create_custom_preset_with())
    assert len(editor.configuration.starting_location.locations) == 2
    assert starting_area_box.checkState() == QtCore.Qt.Checked
    assert intro_world_box.checkState() == QtCore.Qt.PartiallyChecked
    assert blue_key_room_box.checkState() == QtCore.Qt.Unchecked

    # toggle world box
    # don't ask me why qtbot clicks at the wrong position by default on this box
    skip_qtbot.mouseClick(intro_world_box, Qt.LeftButton, pos=QtCore.QPoint(2,intro_world_box.height()/2))
    window.on_preset_changed(editor.create_custom_preset_with())
    assert len(editor.configuration.starting_location.locations) == 3
    assert starting_area_box.checkState() == QtCore.Qt.Checked
    assert intro_world_box.checkState() == QtCore.Qt.Checked
    assert blue_key_room_box.checkState() == QtCore.Qt.Checked

    skip_qtbot.mouseClick(intro_world_box, Qt.LeftButton, pos=QtCore.QPoint(2,intro_world_box.height()/2))
    window.on_preset_changed(editor.create_custom_preset_with())
    assert len(editor.configuration.starting_location.locations) == 0
    assert starting_area_box.checkState() == QtCore.Qt.Unchecked
    assert intro_world_box.checkState() == QtCore.Qt.Unchecked
    assert blue_key_room_box.checkState() == QtCore.Qt.Unchecked
