from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

import pytest
from PySide6 import QtWidgets

from randovania.gui.tracker import tracker_core
from randovania.gui.tracker.tracker_canvas_map import TrackerCanvasMap
from randovania.gui.tracker.tracker_component import TrackerComponent
from randovania.gui.tracker.tracker_configurable_nodes import TrackerConfigurableNodes
from randovania.gui.tracker.tracker_graph_map import TrackerGraphMap
from randovania.gui.tracker.tracker_pickup_inventory import TrackerPickupInventory
from randovania.gui.tracker.tracker_teleporters import TrackerTeleporters
from randovania.gui.tracker.tracker_text_map import TrackerTextMap
from randovania.layout.lib.teleporters import TeleporterShuffleMode
from randovania.lib import json_lib

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
async def tracker(skip_qtbot, tmp_path: Path, default_echoes_preset):
    window = await tracker_core.TrackerWindow.create_new(tmp_path, default_echoes_preset)
    skip_qtbot.add_widget(window)
    return window


def _component_of[T: TrackerComponent](window: tracker_core.TrackerWindow, component_class: type[T]) -> T:
    for component in window.tracker_components:
        if isinstance(component, component_class):
            return component
    raise AssertionError(f"No {component_class.__name__} in the tracker")


async def test_creates_all_components_for_echoes(tracker):
    # Echoes sets hide_database_map_view, so TrackerCanvasMap is not created for it.
    assert [type(component) for component in tracker.tracker_components] == [
        TrackerPickupInventory,
        TrackerTeleporters,
        TrackerConfigurableNodes,
        TrackerTextMap,
        TrackerGraphMap,
    ]


async def test_creates_canvas_map_when_game_allows_it(skip_qtbot, tmp_path: Path, default_prime_preset):
    window = await tracker_core.TrackerWindow.create_new(tmp_path, default_prime_preset)
    skip_qtbot.add_widget(window)

    assert any(isinstance(component, TrackerCanvasMap) for component in window.tracker_components)


async def test_collecting_pickup_refreshes_the_tracker(tracker, tmp_path: Path):
    """Changing a pickup's quantity must reach the window, not just the component."""
    inventory = _component_of(tracker, TrackerPickupInventory)
    pickup = next(it for it in inventory._collected_pickups if it.name == "Space Jump Boots")
    widget = inventory._widget_for_pickup[pickup]
    assert isinstance(widget, QtWidgets.QCheckBox)

    # Run
    widget.setChecked(True)

    # Assert
    persisted = json_lib.read_path(tmp_path.joinpath("state.json"))
    assert persisted["collected_pickups"]["Space Jump Boots"] == 1

    resource = tracker.game_description.resource_database.get_item_by_display_name("Space Jump Boots")
    assert tracker.state_for_current_configuration().resources[resource] == 1


async def test_changing_teleporter_refreshes_the_tracker(
    skip_qtbot, tmp_path: Path, default_echoes_preset, default_echoes_configuration
):
    """Teleporter combos are only editable when they're shuffled, so this needs its own preset."""
    configuration = dataclasses.replace(
        default_echoes_configuration,
        teleporters=dataclasses.replace(
            default_echoes_configuration.teleporters,
            mode=TeleporterShuffleMode.ONE_WAY_ANYTHING,
        ),
    )
    preset = dataclasses.replace(default_echoes_preset.fork(), configuration=configuration)
    tracker = await tracker_core.TrackerWindow.create_new(tmp_path, preset)
    skip_qtbot.add_widget(tracker)

    teleporters = _component_of(tracker, TrackerTeleporters)
    identifier, combo = next(iter(teleporters._teleporter_id_to_combo.items()))
    assert combo.isEnabled()

    # Run
    combo.setCurrentIndex(1)

    # Assert
    persisted = json_lib.read_path(tmp_path.joinpath("state.json"))
    entry = next(it for it in persisted["teleporters"] if it["teleporter"] == identifier.as_json)
    assert entry["data"] == combo.currentData().as_json


async def test_double_clicking_a_node_adds_an_action(tracker):
    """The text map has no access to the action list, it must ask the window for it."""
    text_map = _component_of(tracker, TrackerTextMap)
    current_node = tracker._actions[-1]

    node, item = next(
        (node, text_map._node_to_item[node.node_index])
        for node in tracker.graph.nodes
        if node != current_node and not text_map._node_to_item[node.node_index].isDisabled()
    )

    # Run
    text_map.possible_locations_tree.itemDoubleClicked.emit(item, 0)

    # Assert
    assert tracker._actions[-1] == node
    assert tracker.actions_list.count() == len(tracker._actions)
    assert tracker.undo_last_action_button.isEnabled()


async def test_undo_last_action(tracker):
    text_map = _component_of(tracker, TrackerTextMap)
    node = next(node for node in tracker.graph.nodes if node != tracker._actions[-1])
    tracker._add_new_action(node)

    # Run
    tracker._undo_last_action()

    # Assert
    assert len(tracker._actions) == 1
    assert tracker.actions_list.count() == 1
    assert not tracker.undo_last_action_button.isEnabled()
    assert text_map.current_location_label.text().endswith("Landing Site / Save Station")


async def test_reset_clears_every_component(tracker, tmp_path: Path):
    inventory = _component_of(tracker, TrackerPickupInventory)
    pickup = next(it for it in inventory._collected_pickups if it.name == "Space Jump Boots")
    inventory._widget_for_pickup[pickup].setChecked(True)

    # Run
    tracker.reset()

    # Assert
    assert inventory._collected_pickups[pickup] == 0
    persisted = json_lib.read_path(tmp_path.joinpath("state.json"))
    assert persisted["collected_pickups"]["Space Jump Boots"] == 0
