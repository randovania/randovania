from __future__ import annotations

from pathlib import Path

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
                    "name": "Dark Suit + Light Suit",
                    "row": 0,
                    "column": 0,
                    "resources": ["Dark Suit", "Light Suit"],
                    "kind": "image",
                },
                {
                    "name": "Combat Visor",
                    "row": 2,
                    "column": 0,
                    "resources": ["Combat Visor"],
                    "kind": "image",
                },
                {
                    "name": "Scan Visor",
                    "row": 2,
                    "column": 1,
                    "resources": ["Scan Visor"],
                    "kind": "image",
                },
                {
                    "name": "Dark Visor",
                    "row": 2,
                    "column": 2,
                    "resources": ["Dark Visor"],
                    "kind": "image",
                },
                {
                    "name": "Echo Visor",
                    "row": 2,
                    "column": 3,
                    "resources": ["Echo Visor"],
                    "kind": "image",
                },
                {
                    "name": "Sky Temple Key",
                    "row": 4,
                    "column": 4,
                    "resources": [],
                    "kind": "image",
                },
                {
                    "name": "Sky Temple Key Count",
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
                "Dark Suit + Light Suit": {
                    "image_path": [
                        "game-images/mp2/dark_suit.gif",
                        "game-images/mp2/light_suit.gif",
                    ],
                },
                "Combat Visor": {"image_path": "game-images/mp2/combat_visor.gif"},
                "Scan Visor": {"image_path": "game-images/mp2/scan_visor.gif"},
                "Dark Visor": {"image_path": "game-images/mp2/dark_visor.gif"},
                "Echo Visor": {"image_path": "game-images/mp2/echo_visor.gif"},
                "Sky Temple Key": {"image_path": "game-images/mp2/sky_temple_key.gif"},
            },
            "labels": {
                "Sky Temple Key Count": {"text": "x {amount}/{max_capacity}"},
            },
        }
    )
    widget = ItemTrackerWidget(structure, theme, Path())
    skip_qtbot.addWidget(widget)
    return widget


def test_update_state(widget: ItemTrackerWidget, echoes_resource_database):
    # Setup
    items = echoes_resource_database.item
    inventory = Inventory({items[i]: InventoryItem(i % 3, i % 3) for i in range(len(items))})

    # Run
    widget.update_state(inventory)
