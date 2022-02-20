import re
import typing
from typing import Dict

from randovania.game_description import migration_data
from randovania.games.game import RandovaniaGame
from randovania.lib import migration_lib

CURRENT_VERSION = 10


def _migrate_v1(json_dict: dict) -> dict:
    for game in json_dict["game_modifications"]:
        for hint in game["hints"].values():
            if hint.get("precision") is not None:
                owner = False
                if hint["precision"]["item"] == "owner":
                    owner = True
                    hint["precision"]["item"] = "nothing"
                hint["precision"]["include_owner"] = owner
    return json_dict


def _migrate_v2(json_dict: dict) -> dict:
    for game in json_dict["game_modifications"]:
        for hint in game["hints"].values():
            precision = hint.get("precision")
            if precision is not None and precision.get("relative") is not None:
                precision["relative"]["distance_offset"] = 0
                precision["relative"].pop("precise_distance")
    return json_dict


def _migrate_v3(json_dict: dict) -> dict:
    target_name_re = re.compile(r"(.*) for Player (\d+)")
    if len(json_dict["game_modifications"]) > 1:
        for game in json_dict["game_modifications"]:
            for area in game["locations"].values():
                for location_name, contents in typing.cast(Dict[str, str], area).items():
                    m = target_name_re.match(contents)
                    if m is not None:
                        part_one, part_two = m.group(1, 2)
                        area[location_name] = f"{part_one} for Player {int(part_two) + 1}"
    return json_dict


def _migrate_v4(json_dict: dict) -> dict:
    for game in json_dict["game_modifications"]:
        for world_name, area in game["locations"].items():
            if world_name == "Torvus Bog" and "Portal Chamber/Pickup (Missile)" in area:
                area["Portal Chamber (Light)/Pickup (Missile)"] = area.pop("Portal Chamber/Pickup (Missile)")
        for hint in game["hints"].values():
            if hint["hint_type"] == "location" and hint["precision"]["location"] == "relative-to-area":
                hint["precision"]["relative"]["area_location"] = migration_data.convert_area_loc_id_to_name(
                    RandovaniaGame.METROID_PRIME_ECHOES,  # only echoes has this at the moment
                    hint["precision"]["relative"]["area_location"]
                )

    return json_dict


def _migrate_v5(json_dict: dict) -> dict:
    gate_mapping = {'Hive Access Tunnel': 'Temple Grounds/Hive Access Tunnel/Translator Gate',
                    'Meeting Grounds': 'Temple Grounds/Meeting Grounds/Translator Gate',
                    'Hive Transport Area': 'Temple Grounds/Hive Transport Area/Translator Gate',
                    'Industrial Site': 'Temple Grounds/Industrial Site/Translator Gate',
                    'Path of Eyes': 'Temple Grounds/Path of Eyes/Translator Gate',
                    'Temple Assembly Site': 'Temple Grounds/Temple Assembly Site/Translator Gate',
                    'GFMC Compound': 'Temple Grounds/GFMC Compound/Translator Gate',
                    'Temple Sanctuary (to Sanctuary)': 'Great Temple/Temple Sanctuary/Transport A Translator Gate',
                    'Temple Sanctuary (to Agon)': 'Great Temple/Temple Sanctuary/Transport B Translator Gate',
                    'Temple Sanctuary (to Torvus)': 'Great Temple/Temple Sanctuary/Transport C Translator Gate',
                    'Mining Plaza': 'Agon Wastes/Mining Plaza/Translator Gate',
                    'Mining Station A': 'Agon Wastes/Mining Station A/Translator Gate',
                    'Great Bridge': 'Torvus Bog/Great Bridge/Translator Gate',
                    'Torvus Temple Gate': 'Torvus Bog/Torvus Temple/Translator Gate',
                    'Torvus Temple Elevator': 'Torvus Bog/Torvus Temple/Elevator Translator Scan',
                    'Reactor Core': 'Sanctuary Fortress/Reactor Core/Translator Gate',
                    'Sanctuary Temple': 'Sanctuary Fortress/Sanctuary Temple/Translator Gate'}
    item_mapping = {
        "Scan Visor": "Scan",
        "Violet Translator": "Violet",
        "Amber Translator": "Amber",
        "Emerald Translator": "Emerald",
        "Cobalt Translator": "Cobalt",
    }
    dark_world_mapping = {
        "Dark Agon Wastes": "Agon Wastes",
        "Dark Torvus Bog": "Torvus Bog",
        "Ing Hive": "Sanctuary Fortress",
        "Sky Temple": "Great Temple",
        "Sky Temple Grounds": "Temple Grounds",
    }

    def fix_dark_world(name: str):
        world, rest = name.split("/", 1)
        return f"{dark_world_mapping.get(world, world)}/{rest}"

    def add_teleporter_node(name):
        return migration_data.get_teleporter_area_to_node_mapping()[name]

    for game in json_dict["game_modifications"]:
        game["starting_location"] = fix_dark_world(game["starting_location"])
        game["teleporters"] = {
            add_teleporter_node(fix_dark_world(source)): fix_dark_world(destination)
            for source, destination in game.pop("elevators").items()
        }
        game["configurable_nodes"] = {
            gate_mapping[gate]: {
                "type": "and",
                "data": {
                    "comment": None,
                    "items": [
                        {
                            "type": "resource",
                            "data": {
                                "type": "items",
                                "name": "Scan",
                                "amount": 1,
                                "negate": None
                            }
                        },
                        {
                            "type": "resource",
                            "data": {
                                "type": "items",
                                "name": item_mapping[item],
                                "amount": 1,
                                "negate": None
                            }
                        }
                    ]
                }
            }
            for gate, item in game.pop("translators").items()
        }

    return json_dict


def _migrate_v6(json_dict: dict) -> dict:
    area_name_heuristic = {
        "Tallon Overworld": "prime1",
        "Agon Wastes": "prime2",
        "Bryyo - Fire": "prime3",
        "Norfair": "super_metroid",
        "Artaria": "dread",
    }

    for game in json_dict["game_modifications"]:
        for area_name, identify_game in area_name_heuristic.items():
            if area_name in game["locations"]:
                if identify_game == "prime1":
                    game["locations"]["Frigate Orpheon"] = dict()
                    game["teleporters"][
                        "Frigate Orpheon/Exterior Docking Hangar/Teleport to Landing Site"] = "Tallon Overworld/Landing Site"
                    game["teleporters"][
                        "Impact Crater/Metroid Prime Lair/Teleporter to Credits"] = "End of Game/Credits"
                game["game"] = identify_game
                break
    return json_dict


def _migrate_v7(json_dict: dict) -> dict:
    renamed_items = {
        "3HP Life Capsule": "Small Life Capsule",
        "4HP Life Capsule": "Medium Life Capsule",
        "5HP Life Capsule": "Large Life Capsule",
        "Missile Expansion (24)": "Large Missile Expansion"
    }

    for game in json_dict["game_modifications"]:
        if game["game"] != "cave_story":
            continue
        for world, locations in game["locations"].items():
            game["locations"][world] = {k: renamed_items.get(v, v) for k, v in locations.items()}
        game["starting_items"]["Missiles"] = 5

    return json_dict


def _migrate_v8(json_dict: dict) -> dict:
    json_dict["info"]["randovania_version"] = json_dict["info"].pop("version")
    json_dict["info"]["randovania_version_git"] = "28492915"

    return json_dict


def _migrate_v9(json_dict: dict) -> dict:
    json_dict["info"]["has_spoiler"] = "game_modifications" in json_dict

    return json_dict


_MIGRATIONS = {
    1: _migrate_v1,  # v2.2.0-6-gbfd37022
    2: _migrate_v2,  # v2.4.2-16-g735569fd
    3: _migrate_v3,  # v2.5.2-183-gbf62a4ef
    4: _migrate_v4,  # v3.2.1-40-g94ed9301
    5: _migrate_v5,  # v3.2.1-203-g6e303090
    6: _migrate_v6,
    7: _migrate_v7,  # v3.3.0dev721
    8: _migrate_v8,
    9: _migrate_v9,
}


def convert_to_current_version(json_dict: dict) -> dict:
    return migration_lib.migrate_to_version(
        json_dict,
        CURRENT_VERSION,
        _MIGRATIONS,
    )
