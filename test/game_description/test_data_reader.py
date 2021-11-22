import copy

import pytest

from randovania.game_description.data_reader import WorldReader
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.search import MissingResource
from randovania.games.game import RandovaniaGame


def test_copy_worlds(echoes_game_description):
    game_copy = copy.deepcopy(echoes_game_description)

    assert echoes_game_description.world_list.worlds == game_copy.world_list.worlds
    assert echoes_game_description.world_list.worlds is not game_copy.world_list.worlds


def test_invalid_node_type():
    # Setup
    reader = WorldReader(None, None)

    with pytest.raises(Exception) as e:
        reader.read_node("Broken Node", {
            "heal": True,
            "coordinates": None,
            "description": "",
            "extra": {},
            "node_type": "something that doesn't exist"
        })

    assert str(e.value) == "In node Broken Node, got error: Unknown type: something that doesn't exist"


def test_area_with_invalid_connections():
    # Setup
    db = ResourceDatabase(RandovaniaGame.METROID_PRIME_ECHOES, [], [], [], [], [], [], {}, {}, 0, 0, 0)
    reader = WorldReader(db, None)

    with pytest.raises(MissingResource) as e:
        reader.read_area("Broken Area", {
            "extra": {},
            "nodes": {
                "A": {
                    "heal": True, "coordinates": None, "node_type": "generic",
                    "connections": {}, "extra": {}, "description": "",
                },
                "Broken": {
                    "heal": True, "coordinates": None, "node_type": "generic", "extra": {}, "description": "",
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
                            "items Resource with short_name 'Dark' not found in 0 resources")
