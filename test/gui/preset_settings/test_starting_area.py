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

@pytest.fixture
def setup_and_teardown_for_multiple_nodes(preset_manager):
    # TODO: Currently all areas have only one sp that's why the test is artificially constructed.
    # If we have a real example in the db, the whole setup and teardown can be removed.
    # We need a teardown because the "new_node" needs to be removed otherwise other test will break and
    # it is counterintuitive if other tests break just because this test here fails
    game_desc = default_database.game_description_for(RandovaniaGame.METROID_DREAD)
    world = game_desc.world_list.world_with_name("Artaria")
    area = world.area_by_name("Intro Room")
    test_node_identifier = NodeIdentifier.create(world.name, area.name, "Test Start")
    new_node = GenericNode(test_node_identifier, 0, True, None, "", ("default",), {}, True)
    game_desc.world_list.add_new_node(area, new_node)
    area.nodes.append(new_node)
    yield
    area.nodes.remove(new_node)

def test_area_with_multiple_nodes(skip_qtbot, preset_manager, setup_and_teardown_for_multiple_nodes):
    # Setup
    base = preset_manager.default_preset_for_game(RandovaniaGame.METROID_DREAD).get_preset()
    preset = dataclasses.replace(base, uuid=uuid.UUID('b41fde84-1f57-4b79-8cd6-3e5a78077fa6'))
    editor = PresetEditor(preset)

    game_desc = default_database.game_description_for(preset.game)
    world = game_desc.world_list.world_with_name("Artaria")
    area = world.area_by_name("Intro Room")
                     
    window = PresetMetroidStartingArea(editor, default_database.game_description_for(preset.game), MagicMock())
    skip_qtbot.addWidget(window)
    window.on_preset_changed(editor.create_custom_preset_with())

    start_point = NodeIdentifier.create("Artaria", "Intro Room", "Start Point")
    test_node_identifier = NodeIdentifier.create(world.name, area.name, "Test Start")
    checkbox_node_list = window._starting_location_for_node
    checkbox_area_list = window._starting_location_for_area

    # check default start location is set
    assert checkbox_node_list.get(start_point, None) != None
    assert checkbox_node_list.get(test_node_identifier, None) != None
    assert len(editor.configuration.starting_location.locations) == 1

    # check intro room is PartiallyChecked
    intro_room_box = checkbox_area_list.get(start_point.area_identifier)
    assert intro_room_box != None
    assert intro_room_box.checkState() == QtCore.Qt.PartiallyChecked

    # click "Test Start" and check states
    test_node_checkbox = checkbox_node_list[test_node_identifier]
    skip_qtbot.mouseClick(test_node_checkbox, Qt.LeftButton)
    window.on_preset_changed(editor.create_custom_preset_with())
    assert len(editor.configuration.starting_location.locations) == 2
    assert intro_room_box.checkState() == QtCore.Qt.Checked

    # toggle the area button
    skip_qtbot.mouseClick(intro_room_box, Qt.LeftButton)
    window.on_preset_changed(editor.create_custom_preset_with())
    assert len(editor.configuration.starting_location.locations) == 0
    assert intro_room_box.checkState() == QtCore.Qt.Unchecked

    skip_qtbot.mouseClick(intro_room_box, Qt.LeftButton)
    window.on_preset_changed(editor.create_custom_preset_with())
    assert len(editor.configuration.starting_location.locations) == 2
    assert intro_room_box.checkState() == QtCore.Qt.Checked
