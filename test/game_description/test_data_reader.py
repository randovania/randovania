import pytest

from randovania.game_description.data_reader import WorldReader
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.search import MissingResource
from randovania.games.game import RandovaniaGame


def test_invalid_node_type():
    # Setup
    reader = WorldReader(None, None)
    reader.current_world_name = "World"
    reader.current_area_name = "Area"

    with pytest.raises(Exception) as e:
        reader.read_node("Broken Node", {
            "heal": True,
            "coordinates": None,
            "description": "",
            "extra": {},
            "layers": ["default"],
            "node_type": "something that doesn't exist"
        })

    assert str(e.value) == "In node Broken Node, got error: Unknown type: something that doesn't exist"


def test_area_with_invalid_connections():
    # Setup
    db = ResourceDatabase(RandovaniaGame.METROID_PRIME_ECHOES, [], [], [], [], [], [], {}, {}, 0, 0, 0)
    reader = WorldReader(db, None)
    reader.current_world_name = "World"

    with pytest.raises(MissingResource) as e:
        reader.read_area("Broken Area", {
            "extra": {},
            "nodes": {
                "A": {
                    "heal": True, "coordinates": None, "node_type": "generic",
                    "connections": {}, "extra": {}, "layers": ["default"], "description": "",
                },
                "Broken": {
                    "heal": True, "coordinates": None, "node_type": "generic",
                    "layers": ["default"], "extra": {}, "description": "",
                    "connections": {
                        "A": {
                            "type": "resource",
                            "data": {
                                "type": "items",
                                "name": "Dark",
                                "amount": 1,
                                "negate": False
                            }
                        }
                    }
                },
            }
        })

    assert str(e.value) == ("In area Broken Area, connection from Broken to A got error: "
                            "ITEM Resource with short_name 'Dark' not found in 0 resources")
