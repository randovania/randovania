from __future__ import annotations

import pytest

from randovania.game_description.resources.inventory import Inventory, InventoryItem
from randovania.gui.item_tracker.item_tracker_widget import ItemTrackerWidget
from randovania.gui.item_tracker.tracker_structure import TrackerStructure
from randovania.gui.item_tracker.tracker_theme import TrackerTheme


@pytest.fixture(name="widget")
def item_tracker_widget(skip_qtbot):
    structure = TrackerStructure.model_validate(
        {
            "game": "prime2",
            "elements": [
                {
                    "row": 0,
                    "column": 0,
                    "resources": ["Dark Suit", "Light Suit"],
                    "kind": "image",
                },
                {
                    "row": 2,
                    "column": 0,
                    "resources": ["Combat Visor"],
                    "kind": "image",
                },
                {
                    "row": 2,
                    "column": 1,
                    "resources": ["Scan Visor"],
                    "kind": "image",
                },
                {
                    "row": 2,
                    "column": 2,
                    "resources": ["Dark Visor"],
                    "kind": "image",
                },
                {
                    "row": 2,
                    "column": 3,
                    "resources": ["Echo Visor"],
                    "kind": "image",
                },
                {
                    "row": 4,
                    "column": 4,
                    "resources": [],
                    "kind": "image",
                },
                {
                    "row": 5,
                    "column": 4,
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
                    "kind": "label",
                },
            ],
        }
    )
    theme = TrackerTheme.model_validate(
        {
            "images": {
                "0": {
                    "image_path": [
                        "gui_assets/tracker/game-images/mp2/dark_suit.gif",
                        "gui_assets/tracker/game-images/mp2/light_suit.gif",
                    ],
                },
                "1": {"image_path": "gui_assets/tracker/game-images/mp2/combat_visor.gif"},
                "2": {"image_path": "gui_assets/tracker/game-images/mp2/scan_visor.gif"},
                "3": {"image_path": "gui_assets/tracker/game-images/mp2/dark_visor.gif"},
                "4": {"image_path": "gui_assets/tracker/game-images/mp2/echo_visor.gif"},
                "5": {"image_path": "gui_assets/tracker/game-images/mp2/sky_temple_key.gif"},
            },
            "labels": {
                "6": {"text": "x {amount}/{max_capacity}"},
            },
        }
    )
    widget = ItemTrackerWidget(structure, theme)
    skip_qtbot.addWidget(widget)
    return widget


def test_update_state(widget: ItemTrackerWidget, echoes_resource_database):
    # Setup
    items = echoes_resource_database.item
    inventory = Inventory({items[i]: InventoryItem(i % 3, i % 3) for i in range(len(items))})

    # Run
    widget.update_state(inventory)
