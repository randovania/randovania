import dataclasses

import pytest

from randovania.game_description import data_reader
from randovania.game_description.editor import Editor
from randovania.game_description.requirements import Requirement
from randovania.game_description.world.area_identifier import AreaIdentifier


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

    landing_site = world_list.area_by_area_location(loc)
    source = landing_site.node_with_name("Save Station")
    door = landing_site.node_with_name("Door to Service Access")
    req = landing_site.connections[source][door]

    new_node = dataclasses.replace(door, name="FooBar")

    # Run
    game_editor.replace_node(landing_site, door, new_node)

    # Assert
    assert world_list.area_by_area_location(loc).connections[source][new_node] is req
