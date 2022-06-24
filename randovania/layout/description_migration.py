import re
import typing

from randovania.game_description import migration_data
from randovania.games.game import RandovaniaGame
from randovania.lib import migration_lib

CURRENT_VERSION = 13


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
                for location_name, contents in typing.cast(dict[str, str], area).items():
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


def _migrate_v10(json_dict: dict) -> dict:
    asset_id_conversion = {
        "prime2": {
            '1041207119': 'Sanctuary Fortress/Sanctuary Energy Controller/Lore Scan',
            '1170414603': 'Torvus Bog/Path of Roots/Lore Scan',
            '1238191924': 'Torvus Bog/Gathering Hall/Lore Scan',
            '1394890590': 'Agon Wastes/Mining Station A/Lore Scan',
            '1422425996': 'Torvus Bog/Underground Tunnel/Lore Scan',
            '1489382579': 'Torvus Bog/Torvus Lagoon/Keybearer Corpse (S-Dly)',
            '1657556419': 'Sanctuary Fortress/Sanctuary Entrance/Keybearer Corpse (S-Jrs)',
            '1696621841': 'Temple Grounds/Industrial Site/Keybearer Corpse (J-Fme)',
            '1764636206': 'Agon Wastes/Portal Terminal/Lore Scan',
            '1948976790': 'Sanctuary Fortress/Watch Station/Lore Scan',
            '2190580881': 'Torvus Bog/Catacombs/Lore Scan',
            '2392838062': 'Temple Grounds/Path of Eyes/Lore Scan',
            '2476408598': 'Torvus Bog/Catacombs/Keybearer Corpse (G-Sch)',
            '2558035195': 'Temple Grounds/Meeting Grounds/Lore Scan',
            '2677320745': 'Torvus Bog/Training Chamber/Lore Scan',
            '2725438859': 'Agon Wastes/Mining Station B/Lore Scan',
            '2844827238': 'Sanctuary Fortress/Dynamo Works/Keybearer Corpse (C-Rch)',
            '3212301619': 'Sanctuary Fortress/Main Research/Lore Scan',
            '3277287077': 'Great Temple/Main Energy Controller/Lore Scan',
            '3478732186': 'Temple Grounds/Fortress Transport Access/Lore Scan',
            '3529248034': 'Torvus Bog/Torvus Energy Controller/Lore Scan',
            '353275320': 'Agon Wastes/Central Mining Station/Keybearer Corpse (J-Stl)',
            '3729939997': 'Agon Wastes/Main Reactor/Keybearer Corpse (B-Stl)',
            '3820230591': 'Temple Grounds/Landing Site/Keybearer Corpse (M-Dhe)',
            '4021961856': 'Agon Wastes/Agon Energy Controller/Lore Scan',
            '4072633400': 'Sanctuary Fortress/Sanctuary Entrance/Lore Scan',
            '4115881194': 'Sanctuary Fortress/Main Gyro Chamber/Lore Scan',
            '619091749': 'Agon Wastes/Mining Plaza/Lore Scan',
            '67497535': 'Sanctuary Fortress/Hall of Combat Mastery/Lore Scan',
            '686343194': 'Temple Grounds/Storage Cavern A/Keybearer Corpse (D-Isl)',
            '971220893': 'Temple Grounds/Transport to Agon Wastes/Lore Scan'
        },
        "cave_story": {
            '0': "Egg Corridor/Cthulhu's Abode/Hint - Cthulhu",
            '1': 'Egg Corridor/Egg Corridor/Hint - Blue Robot',
            '10': "Sand Zone/Jenka's House/Hint - Jenka 2",
            '11': 'Ruined Egg Corridor/Little House/Hint - Mrs. Little',
            '12': 'Plantation/Statue Chamber/Hint - Numahachi 1',
            '13': 'Plantation/Statue Chamber/Hint - Numahachi 2',
            '2': 'Grasstown/Grasstown/Hint - Cthulhu (West)',
            '3': 'Grasstown/Grasstown/Hint - Cthulhu (East)',
            '4': 'Labyrinth/Labyrinth I/Hint - Blue Robot (Left)',
            '5': 'Labyrinth/Labyrinth I/Hint - Blue Robot (Right)',
            '6': 'Plantation/Plantation/Hint - Cthulhu',
            '7': 'Ruined Egg Corridor/Egg Corridor?/Hint - Blue Robot',
            '8': 'Grasstown/Power Room/Hint - MALCO',
            '9': "Sand Zone/Jenka's House/Hint - Jenka 1"
        }
    }

    for game in json_dict["game_modifications"]:
        game["hints"] = {
            asset_id_conversion[game["game"]][asset_id]: hint
            for asset_id, hint in game["hints"].items()
        }

    return json_dict


def _migrate_v11(json_dict: dict) -> dict:
    for game in json_dict["game_modifications"]:
        game["dock_weakness"] = {}
        if game["game"] == "dread" and json_dict["info"][0]["configuration"]["extra_pickups_for_bosses"]:
            game["locations"]["Cataris"]["Kraid Arena/Pickup (Kraid)"] = "Energy Transfer Module"

    return json_dict


def _migrate_v12(json_dict: dict) -> dict:
    for game in json_dict["game_modifications"]:
        if game["game"] == "dread":
            game["locations"].pop("Itorash")
            game["starting_items"].pop("Power Beam")
            game["starting_items"].pop("Power Suit")

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
    10: _migrate_v10,
    11: _migrate_v11,
    12: _migrate_v12,
}


def convert_to_current_version(json_dict: dict) -> dict:
    return migration_lib.migrate_to_version(
        json_dict,
        CURRENT_VERSION,
        _MIGRATIONS,
    )
