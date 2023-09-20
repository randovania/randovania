from __future__ import annotations

import dataclasses
import uuid
from unittest.mock import MagicMock

import pytest
from PySide6 import QtCore

from randovania.game_description import default_database
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.games.cave_story.gui.preset_settings.cs_starting_area_tab import PresetCSStartingArea
from randovania.games.game import RandovaniaGame
from randovania.gui.preset_settings.starting_area_tab import PresetMetroidStartingArea, PresetStartingArea
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.base.base_configuration import StartingLocationList


@pytest.mark.parametrize(
    "game", [RandovaniaGame.METROID_PRIME, RandovaniaGame.METROID_PRIME_ECHOES, RandovaniaGame.METROID_PRIME_CORRUPTION]
)
def test_on_preset_changed(skip_qtbot, preset_manager, game):
    # Setup
    base = preset_manager.default_preset_for_game(game).get_preset()
    preset = dataclasses.replace(base, uuid=uuid.UUID("b41fde84-1f57-4b79-8cd6-3e5a78077fa6"))
    options = MagicMock()
    editor = PresetEditor(preset, options)
    window = PresetStartingArea(editor, default_database.game_description_for(preset.game), MagicMock())

    # Run
    window.on_preset_changed(editor.create_custom_preset_with())

    # Assert
    num_areas = len(StartingLocationList.nodes_list(preset.game))
    assert len(window._starting_location_for_area) == num_areas


def test_starting_location_world_select(skip_qtbot, preset_manager):
    # Setup
    base = preset_manager.default_preset_for_game(RandovaniaGame.METROID_PRIME_ECHOES).get_preset()
    preset = dataclasses.replace(base, uuid=uuid.UUID("b41fde84-1f57-4b79-8cd6-3e5a78077fa6"))
    options = MagicMock()
    editor = PresetEditor(preset, options)
    window = PresetMetroidStartingArea(editor, default_database.game_description_for(preset.game), MagicMock())
    skip_qtbot.addWidget(window)

    # Run
    checkbox_list = window._starting_location_for_region
    window.on_preset_changed(editor.create_custom_preset_with())
    assert len(checkbox_list) == 10
    temple_grounds_checkbox = checkbox_list["Temple Grounds"]
    assert temple_grounds_checkbox.checkState() == QtCore.Qt.CheckState.PartiallyChecked

    skip_qtbot.mouseClick(temple_grounds_checkbox, QtCore.Qt.MouseButton.LeftButton)
    assert temple_grounds_checkbox.checkState() == QtCore.Qt.CheckState.Checked
    assert len(editor.configuration.starting_location.locations) == 39

    skip_qtbot.mouseClick(temple_grounds_checkbox, QtCore.Qt.MouseButton.LeftButton)
    assert temple_grounds_checkbox.checkState() == QtCore.Qt.CheckState.Unchecked
    assert len(editor.configuration.starting_location.locations) == 0

    skip_qtbot.mouseClick(temple_grounds_checkbox, QtCore.Qt.MouseButton.LeftButton)
    window.on_preset_changed(editor.create_custom_preset_with())
    assert temple_grounds_checkbox.checkState() == QtCore.Qt.CheckState.Checked
    assert len(editor.configuration.starting_location.locations) == 39


@pytest.mark.parametrize("game_enum", RandovaniaGame)
def test_quick_fill_default(skip_qtbot, preset_manager, game_enum: RandovaniaGame):
    # Setup
    base = preset_manager.default_preset_for_game(game_enum).get_preset()
    preset = dataclasses.replace(base, uuid=uuid.UUID("b41fde84-1f57-4b79-8cd6-3e5a78077fa6"))
    options = MagicMock()
    editor = PresetEditor(preset, options)
    window = PresetStartingArea(editor, default_database.game_description_for(preset.game), MagicMock())
    skip_qtbot.addWidget(window)

    # Run
    skip_qtbot.mouseClick(window.starting_area_quick_fill_default, QtCore.Qt.MouseButton.LeftButton)

    # Assert
    assert editor.configuration.starting_location.locations == (window.game_description.starting_location,)


@pytest.mark.parametrize(
    "game_enum",
    [
        RandovaniaGame.METROID_PRIME,
        RandovaniaGame.METROID_PRIME_ECHOES,
        RandovaniaGame.METROID_DREAD,
    ],
)
def test_quick_fill_save_station(skip_qtbot, preset_manager, game_enum: RandovaniaGame):
    # Setup
    base = preset_manager.default_preset_for_game(game_enum).get_preset()
    preset = dataclasses.replace(base, uuid=uuid.UUID("b41fde84-1f57-4b79-8cd6-3e5a78077fa6"))
    options = MagicMock()
    editor = PresetEditor(preset, options)
    window = PresetMetroidStartingArea(editor, default_database.game_description_for(preset.game), MagicMock())
    skip_qtbot.addWidget(window)

    # Run
    skip_qtbot.mouseClick(window.starting_area_quick_fill_save_station, QtCore.Qt.MouseButton.LeftButton)

    # Assert
    save_stations = tuple(sorted(window._save_station_nodes()))
    assert editor.configuration.starting_location.locations == save_stations


def test_quick_fill_cs_classic(skip_qtbot, preset_manager):
    # Setup
    base = preset_manager.default_preset_for_game(RandovaniaGame.CAVE_STORY).get_preset()
    preset = dataclasses.replace(base, uuid=uuid.UUID("b41fde84-1f57-4b79-8cd6-3e5a78077fa6"))
    options = MagicMock()
    editor = PresetEditor(preset, options)
    window = PresetCSStartingArea(editor, default_database.game_description_for(preset.game), MagicMock())
    skip_qtbot.addWidget(window)

    # Run
    skip_qtbot.mouseClick(window.starting_area_quick_fill_classic, QtCore.Qt.MouseButton.LeftButton)

    # Assert
    expected = {
        NodeIdentifier.create("Mimiga Village", "Start Point", "Room Spawn"),
        NodeIdentifier.create("Mimiga Village", "Arthur's House", "Room Spawn"),
        NodeIdentifier.create("Labyrinth", "Camp", "Room Spawn"),
    }
    assert set(editor.configuration.starting_location.locations) == expected


def test_check_credits(skip_qtbot, preset_manager):
    # Setup
    base = preset_manager.default_preset_for_game(RandovaniaGame.METROID_PRIME).get_preset()
    preset = dataclasses.replace(base, uuid=uuid.UUID("b41fde84-1f57-4b79-8cd6-3e5a78077fa6"))
    options = MagicMock()
    editor = PresetEditor(preset, options)
    window = PresetMetroidStartingArea(editor, default_database.game_description_for(preset.game), MagicMock())
    skip_qtbot.addWidget(window)

    not_expected = NodeIdentifier.create("End of Game", "Credits", "Event - Credits")

    checkbox_list = window._starting_location_for_node
    assert checkbox_list.get(not_expected, None) is None


def test_area_with_multiple_nodes(skip_qtbot, preset_manager):
    # Setup
    base = preset_manager.default_preset_for_game(RandovaniaGame.BLANK).get_preset()
    preset = dataclasses.replace(base, uuid=uuid.UUID("b41fde84-1f57-4b79-8cd6-3e5a78077fa6"))
    options = MagicMock()
    editor = PresetEditor(preset, options)

    game_desc = default_database.game_description_for(preset.game)
    window = PresetStartingArea(editor, default_database.game_description_for(preset.game), MagicMock())
    skip_qtbot.addWidget(window)
    window.on_preset_changed(editor.create_custom_preset_with())

    region = game_desc.region_list.region_with_name("Intro")
    starting_area = region.area_by_name("Starting Area")
    blue_key_room = region.area_by_name("Blue Key Room")

    default_start_point = NodeIdentifier.create(region.name, starting_area.name, "Spawn Point")
    second_start_point = NodeIdentifier.create(region.name, starting_area.name, "Second Spawn Point")
    blue_key_start_point = NodeIdentifier.create(region.name, blue_key_room.name, "Spawn Point")
    checkbox_node_list = window._starting_location_for_node
    checkbox_area_list = window._starting_location_for_area
    checkbox_region_list = window._starting_location_for_region
    starting_area_box = checkbox_area_list.get(default_start_point.area_identifier)
    blue_key_room_box = checkbox_area_list.get(blue_key_start_point.area_identifier)
    intro_world_box = checkbox_region_list.get(region.name)

    # check default start location is set
    assert checkbox_node_list.get(default_start_point, None) is not None
    assert checkbox_node_list.get(second_start_point, None) is not None
    assert checkbox_node_list.get(blue_key_start_point, None) is not None
    assert intro_world_box is not None
    assert starting_area_box is not None
    assert blue_key_room_box is not None
    assert len(editor.configuration.starting_location.locations) == 1

    # test checkboxes
    assert intro_world_box.checkState() == QtCore.Qt.CheckState.PartiallyChecked
    assert starting_area_box.checkState() == QtCore.Qt.CheckState.PartiallyChecked
    assert blue_key_room_box.checkState() == QtCore.Qt.CheckState.Unchecked

    # click "Test Start" and check states
    test_node_checkbox = checkbox_node_list[second_start_point]
    skip_qtbot.mouseClick(test_node_checkbox, QtCore.Qt.MouseButton.LeftButton)
    window.on_preset_changed(editor.create_custom_preset_with())
    assert len(editor.configuration.starting_location.locations) == 2
    assert intro_world_box.checkState() == QtCore.Qt.CheckState.PartiallyChecked
    assert starting_area_box.checkState() == QtCore.Qt.CheckState.Checked
    assert blue_key_room_box.checkState() == QtCore.Qt.CheckState.Unchecked

    # toggle the area button
    skip_qtbot.mouseClick(starting_area_box, QtCore.Qt.MouseButton.LeftButton)
    window.on_preset_changed(editor.create_custom_preset_with())
    assert len(editor.configuration.starting_location.locations) == 0
    assert intro_world_box.checkState() == QtCore.Qt.CheckState.Unchecked
    assert starting_area_box.checkState() == QtCore.Qt.CheckState.Unchecked
    assert blue_key_room_box.checkState() == QtCore.Qt.CheckState.Unchecked

    skip_qtbot.mouseClick(starting_area_box, QtCore.Qt.MouseButton.LeftButton)
    window.on_preset_changed(editor.create_custom_preset_with())
    assert len(editor.configuration.starting_location.locations) == 2
    assert starting_area_box.checkState() == QtCore.Qt.CheckState.Checked
    assert intro_world_box.checkState() == QtCore.Qt.CheckState.PartiallyChecked
    assert blue_key_room_box.checkState() == QtCore.Qt.CheckState.Unchecked

    # toggle db box
    # don't ask me why qtbot clicks at the wrong position by default on this box
    skip_qtbot.mouseClick(
        intro_world_box, QtCore.Qt.MouseButton.LeftButton, pos=QtCore.QPoint(2, intro_world_box.height() // 2)
    )
    window.on_preset_changed(editor.create_custom_preset_with())
    assert len(editor.configuration.starting_location.locations) == 3
    assert starting_area_box.checkState() == QtCore.Qt.CheckState.Checked
    assert intro_world_box.checkState() == QtCore.Qt.CheckState.Checked
    assert blue_key_room_box.checkState() == QtCore.Qt.CheckState.Checked

    skip_qtbot.mouseClick(
        intro_world_box, QtCore.Qt.MouseButton.LeftButton, pos=QtCore.QPoint(2, intro_world_box.height() // 2)
    )
    window.on_preset_changed(editor.create_custom_preset_with())
    assert len(editor.configuration.starting_location.locations) == 0
    assert starting_area_box.checkState() == QtCore.Qt.CheckState.Unchecked
    assert intro_world_box.checkState() == QtCore.Qt.CheckState.Unchecked
    assert blue_key_room_box.checkState() == QtCore.Qt.CheckState.Unchecked
