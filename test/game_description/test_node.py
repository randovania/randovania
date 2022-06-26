from unittest.mock import MagicMock

import pytest

from randovania.game_description.resources.resource_info import ResourceCollection, ResourceInfo
from randovania.game_description.world.logbook_node import LogbookNode
from randovania.game_description.world.node import NodeContext
from randovania.game_description.world.node_identifier import NodeIdentifier


@pytest.fixture(
    params=[False, True],
    name="logbook_node")
def _logbook_node(request, blank_game_description):
    has_translator = request.param
    translator = blank_game_description.resource_database.get_item("BlueKey")

    node = blank_game_description.world_list.node_by_identifier(NodeIdentifier.create(
        "Intro", "Hint Room", "Hint with Translator" if has_translator else "Hint no Translator",
    ))
    assert isinstance(node, LogbookNode)

    return has_translator, translator, node


def test_logbook_node_requirements_to_leave(logbook_node,
                                            empty_patches):
    # Setup
    has_translator, translator, node = logbook_node
    db = empty_patches.game.resource_database

    def ctx(resources):
        return NodeContext(empty_patches, resources, db, empty_patches.game.world_list)

    # Run
    to_leave = node.requirement_to_leave(ctx({}))

    # Assert
    rc2 = ResourceCollection.from_resource_gain(db, [])
    rc3 = ResourceCollection.from_resource_gain(db, [(translator, 1)])

    assert to_leave.satisfied(rc2, 99, None) != has_translator
    assert to_leave.satisfied(rc3, 99, None)


def test_logbook_node_can_collect(logbook_node,
                                  empty_patches):
    # Setup
    db = empty_patches.game.resource_database
    has_translator, translator, node = logbook_node
    node_provider = MagicMock()

    def ctx(*args: ResourceInfo):
        resources = ResourceCollection.from_dict(db, {r: 1 for r in args})
        return NodeContext(empty_patches, resources, db, node_provider)

    assert node.can_collect(ctx()) != has_translator
    assert node.can_collect(ctx(translator))

    resource = node.resource(ctx())
    assert not node.can_collect(ctx(resource))
    assert not node.can_collect(ctx(resource, translator))


def test_logbook_node_resource_gain_on_collect(logbook_node,
                                               empty_patches):
    # Setup
    db = empty_patches.game.resource_database
    node = logbook_node[-1]
    context = NodeContext(empty_patches, ResourceCollection(), db, MagicMock())

    # Run
    gain = node.resource_gain_on_collect(context)

    # Assert
    assert dict(gain) == {node.resource(context): 1}
