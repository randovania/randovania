import pytest

from randovania.game_description import default_database, integrity_check, data_reader
from randovania.games.game import RandovaniaGame
from randovania.lib.enum_lib import iterate_enum


@pytest.mark.parametrize("game_enum", [
    pytest.param(g, marks=pytest.mark.xfail if g.data.experimental else [])
    for g in iterate_enum(RandovaniaGame)
])
def test_find_database_errors(game_enum):
    # Setup
    game = default_database.game_description_for(game_enum)

    # Run
    errors = integrity_check.find_database_errors(game)

    # Assert
    assert errors == []


def test_invalid_db():
    sample_data = {
        "schema_version": 3,
        "game": "prime2",
        "resource_database": {
            "items": [],
            "energy_tank_item_index": 0,
            "item_percentage_index": 0,
            "multiworld_magic_item_index": 0,
            "events": [],
            "tricks": [],
            "damage": [],
            "versions": [],
            "misc": [],
            "requirement_template": {},
            "damage_reductions": [],
        },
        "starting_location": {
            "world_name": "Temple Grounds",
            "area_name": "Landing Site"
        },
        "initial_states": {
            "Default": [
            ]
        },
        "minimal_logic": None,
        "victory_condition": {
            "type": "and",
            "data": {"comment": None, "items": []},
        },
        "dock_weakness_database": {
            "door": [],
            "portal": [],
            "morph_ball": [],
        },
        "worlds": [{
            "name": "World",
            "extra": {},
            "areas": {
                "Area 1": {
                    "default_node": None,
                    "valid_starting_location": False,
                    "extra": {},
                    "nodes": {
                        "Event - Foo": {
                            "node_type": "generic",
                            "heal": False,
                            "coordinates": None,
                            "description": "",
                            "extra": {},
                            "connections": {
                                "Event - Foo": {
                                    "type": "and",
                                    "data": {
                                        "comment": "",
                                        "items": []
                                    }
                                }
                            },
                        },
                        "Door to Area 2 (Generic)": {
                            "node_type": "dock",
                            "heal": False,
                            "coordinates": None,
                            "description": "",
                            "destination": {
                                "world_name": "World",
                                "area_name": "Area 2",
                                "node_name": "Generic Node"
                            },
                            "dock_type": 2,
                            "dock_weakness_index": 0,
                            "extra": {},
                            "connections": {},
                        },
                        "Door to Area 2 (Dock)": {
                            "node_type": "dock",
                            "heal": False,
                            "coordinates": None,
                            "description": "",
                            "destination": {
                                "world_name": "World",
                                "area_name": "Area 2",
                                "node_name": "Door to Area 1"
                            },
                            "dock_type": 2,
                            "dock_weakness_index": 0,
                            "extra": {},
                            "connections": {},
                        }
                    }
                },
                "Area 2": {
                    "default_node": None,
                    "valid_starting_location": False,
                    "extra": {},
                    "nodes": {
                        "Generic Node": {
                            "node_type": "generic",
                            "heal": False,
                            "coordinates": None,
                            "description": "",
                            "extra": {},
                            "connections": {},
                        },
                        "Door to Area 1": {
                            "node_type": "dock",
                            "heal": False,
                            "coordinates": None,
                            "description": "",
                            "destination": {
                                "world_name": "World",
                                "area_name": "Area 1",
                                "node_name": "Door to Area 2 (Generic)"
                            },
                            "dock_type": 2,
                            "dock_weakness_index": 0,
                            "extra": {},
                            "connections": {},
                        }
                    }
                },
            }
        }],
    }
    gd = data_reader.decode_data(sample_data)

    # Run
    errors = integrity_check.find_database_errors(gd)

    # Assert
    assert errors == [
        "World - Area 1 - 'Event - Foo' is not an Event Node, but naming suggests it is",
        "World - Area 1 - Node 'Event - Foo' has a connection to itself",
        "World - Area 1 - 'Door to Area 2 (Generic)' connects to 'world World/area Area 2/node Generic Node'"
        " which is not a DockNode",
        "World - Area 1 - 'Door to Area 2 (Dock)' connects to 'world World/area Area 2/node Door to Area 1',"
        " but that dock connects to 'world World/area Area 1/node Door to Area 2 (Generic)' instead.",
        "World - Area 2 - 'Door to Area 1' connects to 'world World/area Area 1/node Door to Area 2 (Generic)',"
        " but that dock connects to 'world World/area Area 2/node Generic Node' instead."
    ]
