from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from randovania.game_description.data_reader import RegionReader
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.search import MissingResource
from randovania.games.game import RandovaniaGame


def test_invalid_node_type():
    # Setup
    reader = RegionReader(MagicMock(), MagicMock())
    reader.current_region_name = "World"
    reader.current_area_name = "Area"

    with pytest.raises(Exception, match="In node Broken Node, got error: Unknown type: something that doesn't exist"):
        reader.read_node(
            "Broken Node",
            {
                "heal": True,
                "coordinates": None,
                "description": "",
                "extra": {},
                "layers": ["default"],
                "node_type": "something that doesn't exist",
                "valid_starting_location": False,
            },
        )


def test_area_with_invalid_connections():
    # Setup
    db = ResourceDatabase(
        RandovaniaGame.METROID_PRIME_ECHOES,
        [],
        [],
        [],
        [],
        [],
        [],
        {},
        damage_reductions={},
        energy_tank_item=MagicMock(),
    )
    reader = RegionReader(db, MagicMock())
    reader.current_region_name = "World"

    with pytest.raises(MissingResource) as e:
        reader.read_area(
            "Broken Area",
            {
                "extra": {},
                "nodes": {
                    "A": {
                        "heal": True,
                        "coordinates": None,
                        "node_type": "generic",
                        "valid_starting_location": False,
                        "connections": {},
                        "extra": {},
                        "layers": ["default"],
                        "description": "",
                    },
                    "Broken": {
                        "heal": True,
                        "coordinates": None,
                        "node_type": "generic",
                        "valid_starting_location": False,
                        "layers": ["default"],
                        "extra": {},
                        "description": "",
                        "connections": {
                            "A": {
                                "type": "resource",
                                "data": {"type": "items", "name": "Dark", "amount": 1, "negate": False},
                            }
                        },
                    },
                },
            },
        )

    assert str(e.value) == (
        "In area Broken Area, connection from Broken to A got error: "
        "ITEM Resource with short_name 'Dark' not found in 0 resources"
    )
