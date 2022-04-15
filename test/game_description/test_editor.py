import dataclasses

import pytest

from randovania.game_description import data_reader
from randovania.game_description.editor import Editor
from randovania.game_description.requirements import Requirement
from randovania.game_description.world.area_identifier import AreaIdentifier
from randovania.game_description.world.dock_node import DockNode


@pytest.fixture(name="game_editor")
def _editor(echoes_game_data):
    return Editor(data_reader.decode_data(echoes_game_data))


def test_edit_connections(game_editor):
    # Setup
    landing_site = game_editor.game.world_list.area_by_area_location(AreaIdentifier("Temple Grounds", "Landing Site"))
    source = landing_site.node_with_name("Save Station")
    target = landing_site.node_with_name("Door to Service Access")
    assert landing_site.connections[source][target] != Requirement.trivial()

    # Run
    game_editor.edit_connections(landing_site, source, target, Requirement.trivial())

    # Assert
    assert landing_site.connections[source][target] == Requirement.trivial()


def test_remove_node(game_editor):
    # Setup
    world_list = game_editor.game.world_list
    loc = AreaIdentifier("Temple Grounds", "Landing Site")

    landing_site = world_list.area_by_area_location(loc)
    node = landing_site.node_with_name("Door to Service Access")
    assert node is not None

    # Run
    game_editor.remove_node(landing_site, node)

    # Assert
    assert world_list.area_by_area_location(loc).node_with_name("Door to Service Access") is None


def test_replace_node(game_editor):
    # Setup
    world_list = game_editor.game.world_list
    loc = AreaIdentifier("Temple Grounds", "Landing Site")
    loc2 = AreaIdentifier("Temple Grounds", "Service Access")

    landing_site = world_list.area_by_area_location(loc)
    source = landing_site.node_with_name("Save Station")
    door = landing_site.node_with_name("Door to Service Access")
    req = landing_site.connections[source][door]

    new_node = dataclasses.replace(door, identifier=door.identifier.renamed("FooBar"))

    # Run
    game_editor.replace_node(landing_site, door, new_node)

    # Assert
    assert world_list.area_by_area_location(loc).connections[source][new_node] is req
    dock_to_landing = world_list.area_by_area_location(loc2).node_with_name("Door to Landing Site")
    assert isinstance(dock_to_landing, DockNode)
    assert dock_to_landing.default_connection.node_name == "FooBar"


def test_replace_node_unknown_node(game_editor):
    # Setup
    world_list = game_editor.game.world_list
    loc = AreaIdentifier("Temple Grounds", "Landing Site")
    loc2 = AreaIdentifier("Temple Grounds", "Service Access")

    landing_site = world_list.area_by_area_location(loc)
    dock = world_list.area_by_area_location(loc2).node_with_name("Door to Landing Site")

    # Run
    with pytest.raises(ValueError, match="Given Door to Landing Site does does not belong to Landing Site."):
        game_editor.replace_node(landing_site, dock, dock)


def test_rename_area(game_editor):
    # Setup
    world_list = game_editor.game.world_list
    loc_1 = AreaIdentifier("Temple Grounds", "Transport to Agon Wastes")
    loc_2 = AreaIdentifier("Agon Wastes", "Transport to Temple Grounds")
    final = AreaIdentifier("Temple Grounds", "Foo Bar Transportation")

    # Run
    game_editor.rename_area(world_list.area_by_area_location(loc_1),
                            "Foo Bar Transportation")

    # Assert
    assert world_list.area_by_area_location(final) is not None
    area_2 = world_list.area_by_area_location(loc_2)
    assert area_2.node_with_name("Elevator to Temple Grounds - Foo Bar Transportation") is not None
