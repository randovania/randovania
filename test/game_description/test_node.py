import pytest

from randovania.game_description.world.node import LogbookNode, LoreType
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.resource_info import convert_resource_gain_to_current_resources


@pytest.fixture(
    params=[False, True],
    name="logbook_node")
def _logbook_node(request):
    has_translator = request.param
    scan_visor = ItemResourceInfo(1, "Scan", "S", 1, None)
    translator = ItemResourceInfo(2, "Translator", "T", 1, None)

    node = LogbookNode("Logbook", False, None, 0,
                       1000, scan_visor, LoreType.LUMINOTH_LORE,
                       translator if has_translator else None, None)

    return has_translator, scan_visor, translator, node


def test_logbook_node_requirements_to_leave(logbook_node,
                                            empty_patches):
    # Setup
    has_translator, scan_visor, translator, node = logbook_node

    # Run
    to_leave = node.requirement_to_leave(empty_patches, {})

    # Assert
    assert not to_leave.satisfied({}, 99, None)
    assert to_leave.satisfied({scan_visor: 1}, 99, None) != has_translator
    assert to_leave.satisfied({scan_visor: 1, translator: 1}, 99, None)


def test_logbook_node_can_collect(logbook_node,
                                  empty_patches):
    # Setup
    has_translator, scan_visor, translator, node = logbook_node

    assert not node.can_collect(empty_patches, {}, (), None)
    assert node.can_collect(empty_patches, {scan_visor: 1}, (), None) != has_translator
    assert node.can_collect(empty_patches, {scan_visor: 1, translator: 1}, (), None)

    resource = node.resource()
    assert not node.can_collect(empty_patches, {resource: 1}, (), None)
    assert not node.can_collect(empty_patches, {resource: 1, scan_visor: 1}, (), None)
    assert not node.can_collect(empty_patches, {resource: 1, scan_visor: 1, translator: 1}, (), None)


def test_logbook_node_resource_gain_on_collect(logbook_node,
                                               empty_patches):
    # Setup
    node = logbook_node[-1]

    # Run
    gain = node.resource_gain_on_collect(empty_patches, {}, (), None)

    # Assert
    assert convert_resource_gain_to_current_resources(gain) == {node.resource(): 1}
