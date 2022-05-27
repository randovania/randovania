from unittest.mock import MagicMock

import pytest

from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.resource_info import ResourceCollection, ResourceInfo
from randovania.game_description.world.logbook_node import LoreType, LogbookNode
from randovania.game_description.world.node import NodeContext
from randovania.game_description.world.node_identifier import NodeIdentifier


@pytest.fixture(
    params=[False, True],
    name="logbook_node")
def _logbook_node(request):
    has_translator = request.param
    scan_visor = ItemResourceInfo("Scan", "S", 1, None)
    translator = ItemResourceInfo("Translator", "T", 1, None)

    node = LogbookNode(NodeIdentifier.create("W", "A", "Logbook"),
                       False, None, "", ("default",), {},
                       1000, scan_visor, LoreType.REQUIRES_ITEM,
                       translator if has_translator else None, None)

    return has_translator, scan_visor, translator, node


def test_logbook_node_requirements_to_leave(logbook_node,
                                            empty_patches):
    # Setup
    has_translator, scan_visor, translator, node = logbook_node
    node_provider = MagicMock()

    def ctx(resources):
        return NodeContext(empty_patches, resources, MagicMock(), node_provider)

    # Run
    to_leave = node.requirement_to_leave(ctx({}))

    # Assert
    rc1 = ResourceCollection()
    rc2 = ResourceCollection.from_resource_gain([(scan_visor, 1)])
    rc3 = ResourceCollection.from_resource_gain([(scan_visor, 1), (translator, 1)])

    assert not to_leave.satisfied(rc1, 99, None)
    assert to_leave.satisfied(rc2, 99, None) != has_translator
    assert to_leave.satisfied(rc3, 99, None)


def test_logbook_node_can_collect(logbook_node,
                                  empty_patches):
    # Setup
    has_translator, scan_visor, translator, node = logbook_node
    node_provider = MagicMock()

    def ctx(*args: ResourceInfo):
        resources = ResourceCollection.from_dict({r: 1 for r in args})
        return NodeContext(empty_patches, resources, MagicMock(), node_provider)

    assert not node.can_collect(ctx())
    assert node.can_collect(ctx(scan_visor)) != has_translator
    assert node.can_collect(ctx(scan_visor, translator))

    resource = node.resource(ctx())
    assert not node.can_collect(ctx(resource))
    assert not node.can_collect(ctx(resource, scan_visor))
    assert not node.can_collect(ctx(resource, scan_visor, translator))


def test_logbook_node_resource_gain_on_collect(logbook_node,
                                               empty_patches):
    # Setup
    node = logbook_node[-1]
    context = NodeContext(empty_patches, ResourceCollection(), None, MagicMock())

    # Run
    gain = node.resource_gain_on_collect(context)

    # Assert
    assert dict(gain) == {node.resource(context): 1}
