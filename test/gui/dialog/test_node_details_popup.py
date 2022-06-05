import pytest

from randovania.game_description.world.node import GenericNode
from randovania.game_description.world.configurable_node import ConfigurableNode
from randovania.game_description.world.teleporter_node import TeleporterNode
from randovania.game_description.world.dock_node import DockNode
from randovania.game_description.world.player_ship_node import PlayerShipNode
from randovania.game_description.world.logbook_node import LogbookNode
from randovania.game_description.world.event_node import EventNode
from randovania.game_description.world.pickup_node import PickupNode
from randovania.gui.dialog.node_details_popup import NodeDetailsPopup


@pytest.mark.parametrize("node_type", [
    GenericNode,
    DockNode,
    PickupNode,
    TeleporterNode,
    EventNode,
    ConfigurableNode,
    LogbookNode,
])
def test_unchanged_create_new_node_echoes(skip_qtbot, echoes_game_description, node_type):
    node = next(node for node in echoes_game_description.world_list.iterate_nodes() if isinstance(node, node_type))
    dialog = NodeDetailsPopup(echoes_game_description, node)

    # Run
    new_node = dialog.create_new_node()

    # Assert
    assert node == new_node


@pytest.mark.parametrize("node_type", [
    PlayerShipNode,
])
def test_unchanged_create_new_node_corruption(skip_qtbot, corruption_game_description, node_type):
    node = next(node for node in corruption_game_description.world_list.iterate_nodes() if isinstance(node, node_type))
    dialog = NodeDetailsPopup(corruption_game_description, node)

    # Run
    new_node = dialog.create_new_node()

    # Assert
    assert node == new_node
