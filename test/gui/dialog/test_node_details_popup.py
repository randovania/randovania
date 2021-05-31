import pytest

from randovania.game_description.world.node import GenericNode, DockNode, PickupNode, TeleporterNode, EventNode, \
    TranslatorGateNode, LogbookNode, PlayerShipNode
from randovania.gui.dialog.node_details_popup import NodeDetailsPopup


@pytest.mark.parametrize("node_type", [
    GenericNode,
    DockNode,
    PickupNode,
    TeleporterNode,
    EventNode,
    TranslatorGateNode,
    LogbookNode,
])
def test_unchanged_create_new_node_echoes(skip_qtbot, echoes_game_description, node_type):
    node = next(node for node in echoes_game_description.world_list.all_nodes if isinstance(node, node_type))
    dialog = NodeDetailsPopup(echoes_game_description, node)

    # Run
    new_node = dialog.create_new_node()

    # Assert
    assert node == new_node


@pytest.mark.parametrize("node_type", [
    PlayerShipNode,
])
def test_unchanged_create_new_node_corruption(skip_qtbot, corruption_game_description, node_type):
    node = next(node for node in corruption_game_description.world_list.all_nodes if isinstance(node, node_type))
    dialog = NodeDetailsPopup(corruption_game_description, node)

    # Run
    new_node = dialog.create_new_node()

    # Assert
    assert node == new_node
