from __future__ import annotations

import pytest

from randovania.game_description.resources.inventory import Inventory, InventoryItem
from randovania.gui.widgets.item_tracker_widget import ItemTrackerWidget


@pytest.fixture(name="widget")
def item_tracker_widget(skip_qtbot):
    widget = ItemTrackerWidget(
        {
            "game": "prime2",
            "elements": [
                {
                    "row": 0,
                    "column": 0,
                    "resources": ["Dark Suit", "Light Suit"],
                    "image_path": [
                        "gui_assets/tracker/game-images/mp2/dark_suit.gif",
                        "gui_assets/tracker/game-images/mp2/light_suit.gif",
                    ],
                },
                {
                    "row": 2,
                    "column": 0,
                    "resources": ["Combat Visor"],
                    "image_path": "gui_assets/tracker/game-images/mp2/combat_visor.gif",
                },
                {
                    "row": 2,
                    "column": 1,
                    "resources": ["Scan Visor"],
                    "image_path": "gui_assets/tracker/game-images/mp2/scan_visor.gif",
                },
                {
                    "row": 2,
                    "column": 2,
                    "resources": ["Dark Visor"],
                    "image_path": "gui_assets/tracker/game-images/mp2/dark_visor.gif",
                },
                {
                    "row": 2,
                    "column": 3,
                    "resources": ["Echo Visor"],
                    "image_path": "gui_assets/tracker/game-images/mp2/echo_visor.gif",
                },
                {
                    "row": 4,
                    "column": 4,
                    "resources": [],
                    "image_path": "gui_assets/tracker/game-images/mp2/sky_temple_key.gif",
                },
                {
                    "row": 5,
                    "column": 4,
                    "label": "x {amount}/{max_capacity}",
                    "resources": [
                        "Sky Temple Key 1",
                        "Sky Temple Key 2",
                        "Sky Temple Key 3",
                        "Sky Temple Key 4",
                        "Sky Temple Key 5",
                        "Sky Temple Key 6",
                        "Sky Temple Key 7",
                        "Sky Temple Key 8",
                        "Sky Temple Key 9",
                    ],
                },
            ],
        }
    )
    skip_qtbot.addWidget(widget)
    return widget


def test_update_state(widget: ItemTrackerWidget, echoes_resource_database):
    # Setup
    items = echoes_resource_database.item
    inventory = Inventory({items[i]: InventoryItem(i % 3, i % 3) for i in range(len(items))})

    # Run
    widget.update_state(inventory)
