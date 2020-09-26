import pytest

from randovania.game_description.node import GenericNode, DockNode, PickupNode, TeleporterNode, EventNode, \
    TranslatorGateNode, LogbookNode
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
def test_unchanged_create_new_node(skip_qtbot, echoes_game_description, node_type):
    node = next(node for node in echoes_game_description.world_list.all_nodes if isinstance(node, node_type))
    dialog = NodeDetailsPopup(echoes_game_description, node)

    # Run
    new_node = dialog.create_new_node()

    # Assert
    assert node == new_node
