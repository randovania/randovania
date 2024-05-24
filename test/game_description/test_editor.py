from __future__ import annotations

import dataclasses

import pytest

from randovania.game_description import data_reader
from randovania.game_description.db.area_identifier import AreaIdentifier
from randovania.game_description.db.dock_node import DockNode
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.game_description.editor import Editor
from randovania.game_description.requirements.base import Requirement
from randovania.game_description.requirements.node_requirement import NodeRequirement
from randovania.game_description.resources.resource_collection import ResourceCollection
from randovania.game_description.resources.resource_database import NamedRequirementTemplate


@pytest.fixture()
def game_editor(echoes_game_data):
    return Editor(data_reader.decode_data(echoes_game_data))


def test_edit_connections(game_editor):
    # Setup
    landing_site = game_editor.game.region_list.area_by_area_location(AreaIdentifier("Temple Grounds", "Landing Site"))
    source = landing_site.node_with_name("Save Station")
    target = landing_site.node_with_name("Door to Service Access")
    assert landing_site.connections[source][target] != Requirement.trivial()

    # Run
    game_editor.edit_connections(landing_site, source, target, Requirement.trivial())

    # Assert
    assert landing_site.connections[source][target] == Requirement.trivial()


def test_remove_node(game_editor):
    # Setup
    region_list = game_editor.game.region_list
    loc = AreaIdentifier("Temple Grounds", "Landing Site")

    landing_site = region_list.area_by_area_location(loc)
    node = landing_site.node_with_name("Door to Service Access")
    assert node is not None

    # Run
    game_editor.remove_node(landing_site, node)

    # Assert
    assert region_list.area_by_area_location(loc).node_with_name("Door to Service Access") is None


def test_replace_node(game_editor):
    # Setup
    region_list = game_editor.game.region_list
    loc = AreaIdentifier("Temple Grounds", "Landing Site")
    loc2 = AreaIdentifier("Temple Grounds", "Service Access")

    landing_site = region_list.area_by_area_location(loc)
    source = landing_site.node_with_name("Save Station")
    door = landing_site.node_with_name("Door to Service Access")
    assert isinstance(door, DockNode)
    req = landing_site.connections[source][door]

    new_node = dataclasses.replace(door, identifier=door.identifier.renamed("FooBar"))

    # Run
    game_editor.replace_node(landing_site, door, new_node)

    # Assert
    assert region_list.area_by_area_location(loc).connections[source][new_node] is req
    dock_to_landing = region_list.area_by_area_location(loc2).node_with_name("Door to Landing Site")
    assert isinstance(dock_to_landing, DockNode)
    assert dock_to_landing.default_connection.node == "FooBar"


def test_replace_generic_node_with_dock(game_editor):
    # Setup
    region_list = game_editor.game.region_list
    loc = AreaIdentifier("Temple Grounds", "Landing Site")

    landing_site = region_list.area_by_area_location(loc)
    source = landing_site.node_with_name("Save Station")
    door = landing_site.node_with_name("Door to Service Access")
    assert isinstance(door, DockNode)

    new_node = dataclasses.replace(door, identifier=door.identifier.renamed("FooBar"))

    # Run
    game_editor.replace_node(landing_site, source, new_node)

    # Assert
    assert landing_site.node_with_name("Save Station") is None
    assert landing_site.node_with_name("FooBar") is new_node


def test_replace_node_unknown_node(game_editor):
    # Setup
    region_list = game_editor.game.region_list
    loc = AreaIdentifier("Temple Grounds", "Landing Site")
    loc2 = AreaIdentifier("Temple Grounds", "Service Access")

    landing_site = region_list.area_by_area_location(loc)
    dock = region_list.area_by_area_location(loc2).node_with_name("Door to Landing Site")

    # Run
    with pytest.raises(ValueError, match="Given Door to Landing Site does does not belong to Landing Site."):
        game_editor.replace_node(landing_site, dock, dock)


def test_rename_area(game_editor):
    # Setup
    new_area_name = "Foo Bar Transportation"
    region_list = game_editor.game.region_list
    loc_1 = AreaIdentifier("Temple Grounds", "Transport to Agon Wastes")
    loc_2 = AreaIdentifier("Agon Wastes", "Transport to Temple Grounds")
    final = AreaIdentifier("Temple Grounds", new_area_name)

    # Run
    game_editor.rename_area(region_list.area_by_area_location(loc_1), new_area_name)

    # Assert
    assert region_list.area_by_area_location(final) is not None
    area_2 = region_list.area_by_area_location(loc_2)
    dock_node = area_2.node_with_name("Elevator to Temple Grounds")
    assert dock_node is not None
    assert isinstance(dock_node, DockNode)
    assert dock_node.default_connection.area == new_area_name


def test_rename_lock_used_in_node_requirement(game_editor: Editor) -> None:
    game_editor.game.resource_database.requirement_template["Special Requirement Template"] = NamedRequirementTemplate(
        "Special Requirement Template",
        NodeRequirement(
            NodeIdentifier.create(
                "Great Temple",
                "Transport A Access",
                "Lock - Door to Temple Sanctuary",
            )
        ),
    )
    region_list = game_editor.game.region_list
    node = region_list.node_by_identifier(
        NodeIdentifier.create(
            "Great Temple",
            "Transport A Access",
            "Door to Temple Sanctuary",
        )
    )
    area = region_list.nodes_to_area(node)

    # Run
    game_editor.rename_node(area, node, "Door to Temple Sanctuary (Weird)")

    # Assert
    template = game_editor.game.resource_database.requirement_template["Special Requirement Template"]
    context = game_editor.game.create_node_context(ResourceCollection())
    assert list(template.requirement.iterate_resource_requirements(context)) != []
