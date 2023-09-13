from __future__ import annotations

import pytest
from PySide6.QtCore import Qt

from randovania.game_description.db.configurable_node import ConfigurableNode
from randovania.game_description.db.dock_node import DockNode
from randovania.game_description.db.event_node import EventNode
from randovania.game_description.db.hint_node import HintNode
from randovania.game_description.db.node import GenericNode
from randovania.game_description.db.pickup_node import PickupNode
from randovania.game_description.db.teleporter_network_node import TeleporterNetworkNode
from randovania.gui.dialog.node_details_popup import NodeDetailsPopup


@pytest.mark.parametrize(
    "node_type",
    [
        GenericNode,
        DockNode,
        PickupNode,
        EventNode,
        ConfigurableNode,
        HintNode,
    ],
)
def test_unchanged_create_new_node_echoes(skip_qtbot, echoes_game_description, node_type):
    node = next(node for node in echoes_game_description.region_list.iterate_nodes() if isinstance(node, node_type))
    dialog = NodeDetailsPopup(echoes_game_description, node)
    skip_qtbot.addWidget(dialog)

    # Run
    new_node = dialog.create_new_node()

    # Assert
    assert node == new_node


@pytest.mark.parametrize(
    "node_type",
    [
        TeleporterNetworkNode,
    ],
)
def test_unchanged_create_new_node_corruption(skip_qtbot, corruption_game_description, node_type):
    node = next(node for node in corruption_game_description.region_list.iterate_nodes() if isinstance(node, node_type))
    dialog = NodeDetailsPopup(corruption_game_description, node)
    skip_qtbot.addWidget(dialog)

    # Run
    new_node = dialog.create_new_node()

    # Assert
    assert node == new_node


def test_change_incompatible_dock_list(skip_qtbot, echoes_game_description):
    node = next(node for node in echoes_game_description.region_list.iterate_nodes() if isinstance(node, DockNode))
    dialog = NodeDetailsPopup(echoes_game_description, node)
    skip_qtbot.addWidget(dialog)
    model = dialog.dock_incompatible_model

    m = model.index(0)
    assert model.data(m, Qt.ItemDataRole.WhatsThisRole) is None
    assert model.data(m, Qt.ItemDataRole.DisplayRole) == "New..."
    assert model.data(m, Qt.ItemDataRole.EditRole) == ""

    assert not model.setData(m, "Normal Door", Qt.ItemDataRole.DisplayRole)
    assert model.data(m, Qt.ItemDataRole.DisplayRole) == "New..."

    assert model.setData(m, "Normal Door", Qt.ItemDataRole.EditRole)

    assert model.data(m, Qt.ItemDataRole.DisplayRole) == "Normal Door"

    result = dialog.create_new_node()
    assert isinstance(result, DockNode)
    assert [w.name for w in result.incompatible_dock_weaknesses] == ["Normal Door"]

    assert model.removeRow(0, m)
    assert model.data(m, Qt.ItemDataRole.EditRole) == ""

    result = dialog.create_new_node()
    assert isinstance(result, DockNode)
    assert [w.name for w in result.incompatible_dock_weaknesses] == []


def test_on_pickup_index_button_generic(skip_qtbot, echoes_game_description):
    node = next(node for node in echoes_game_description.region_list.iterate_nodes() if isinstance(node, GenericNode))
    dialog = NodeDetailsPopup(echoes_game_description, node)
    skip_qtbot.addWidget(dialog)

    dialog.on_pickup_index_button()
    assert dialog.pickup_index_spin.value() == 119


def test_on_pickup_index_button_pickup(skip_qtbot, echoes_game_description):
    node = next(node for node in echoes_game_description.region_list.iterate_nodes() if isinstance(node, PickupNode))
    dialog = NodeDetailsPopup(echoes_game_description, node)
    skip_qtbot.addWidget(dialog)

    dialog.on_pickup_index_button()
    assert dialog.pickup_index_spin.value() == node.pickup_index.index


def test_on_dock_update_name_button(skip_qtbot, blank_game_description):
    node = next(node for node in blank_game_description.region_list.iterate_nodes() if isinstance(node, DockNode))
    dialog = NodeDetailsPopup(blank_game_description, node)
    skip_qtbot.addWidget(dialog)
    dialog.name_edit.setText("Weird Name")

    # Run
    assert dialog.name_edit.text() == "Weird Name"
    dialog.on_dock_update_name_button()
    assert dialog.name_edit.text() == node.name
