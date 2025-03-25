from __future__ import annotations

import re
import typing

from randovania.game.game_enum import RandovaniaGame
from randovania.game_description import migration_data
from randovania.lib import migration_lib


def _migrate_v1(json_dict: dict) -> None:
    for game in json_dict["game_modifications"]:
        for hint in game["hints"].values():
            if hint.get("precision") is not None:
                owner = False
                if hint["precision"]["item"] == "owner":
                    owner = True
                    hint["precision"]["item"] = "nothing"
                hint["precision"]["include_owner"] = owner


def _migrate_v2(json_dict: dict) -> None:
    for game in json_dict["game_modifications"]:
        for hint in game["hints"].values():
            precision = hint.get("precision")
            if precision is not None and precision.get("relative") is not None:
                precision["relative"]["distance_offset"] = 0
                precision["relative"].pop("precise_distance")


def _migrate_v3(json_dict: dict) -> None:
    target_name_re = re.compile(r"(.*) for Player (\d+)")
    if len(json_dict["game_modifications"]) > 1:
        for game in json_dict["game_modifications"]:
            for area in game["locations"].values():
                for location_name, contents in typing.cast("dict[str, str]", area).items():
                    m = target_name_re.match(contents)
                    if m is not None:
                        part_one, part_two = m.group(1, 2)
                        area[location_name] = f"{part_one} for Player {int(part_two) + 1}"


def _migrate_v4(json_dict: dict) -> None:
    for game in json_dict["game_modifications"]:
        for world_name, area in game["locations"].items():
            if world_name == "Torvus Bog" and "Portal Chamber/Pickup (Missile)" in area:
                area["Portal Chamber (Light)/Pickup (Missile)"] = area.pop("Portal Chamber/Pickup (Missile)")
        for hint in game["hints"].values():
            if hint["hint_type"] == "location" and hint["precision"]["location"] == "relative-to-area":
                hint["precision"]["relative"]["area_location"] = migration_data.convert_area_loc_id_to_name(
                    RandovaniaGame.METROID_PRIME_ECHOES,  # only echoes has this at the moment
                    hint["precision"]["relative"]["area_location"],
                )


def _migrate_v5(json_dict: dict) -> None:
    gate_mapping = {
        "Hive Access Tunnel": "Temple Grounds/Hive Access Tunnel/Translator Gate",
        "Meeting Grounds": "Temple Grounds/Meeting Grounds/Translator Gate",
        "Hive Transport Area": "Temple Grounds/Hive Transport Area/Translator Gate",
        "Industrial Site": "Temple Grounds/Industrial Site/Translator Gate",
        "Path of Eyes": "Temple Grounds/Path of Eyes/Translator Gate",
        "Temple Assembly Site": "Temple Grounds/Temple Assembly Site/Translator Gate",
        "GFMC Compound": "Temple Grounds/GFMC Compound/Translator Gate",
        "Temple Sanctuary (to Sanctuary)": "Great Temple/Temple Sanctuary/Transport A Translator Gate",
        "Temple Sanctuary (to Agon)": "Great Temple/Temple Sanctuary/Transport B Translator Gate",
        "Temple Sanctuary (to Torvus)": "Great Temple/Temple Sanctuary/Transport C Translator Gate",
        "Mining Plaza": "Agon Wastes/Mining Plaza/Translator Gate",
        "Mining Station A": "Agon Wastes/Mining Station A/Translator Gate",
        "Great Bridge": "Torvus Bog/Great Bridge/Translator Gate",
        "Torvus Temple Gate": "Torvus Bog/Torvus Temple/Translator Gate",
        "Torvus Temple Elevator": "Torvus Bog/Torvus Temple/Elevator Translator Scan",
        "Reactor Core": "Sanctuary Fortress/Reactor Core/Translator Gate",
        "Sanctuary Temple": "Sanctuary Fortress/Sanctuary Temple/Translator Gate",
    }
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

    def fix_dark_world(name: str) -> str:
        world, rest = name.split("/", 1)
        return f"{dark_world_mapping.get(world, world)}/{rest}"

    def add_teleporter_node(name: str) -> str:
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
                        {"type": "resource", "data": {"type": "items", "name": "Scan", "amount": 1, "negate": False}},
                        {
                            "type": "resource",
                            "data": {"type": "items", "name": item_mapping[item], "amount": 1, "negate": False},
                        },
                    ],
                },
            }
            for gate, item in game.pop("translators").items()
        }


def _migrate_v6(json_dict: dict) -> None:
    area_name_heuristic = {
        "Tallon Overworld": "prime1",
        "Agon Wastes": "prime2",
        "Artaria": "dread",
    }

    for game in json_dict["game_modifications"]:
        for area_name, identify_game in area_name_heuristic.items():
            if area_name in game["locations"]:
                if identify_game == "prime1":
                    game["locations"]["Frigate Orpheon"] = {}
                    game["teleporters"]["Frigate Orpheon/Exterior Docking Hangar/Teleport to Landing Site"] = (
                        "Tallon Overworld/Landing Site"
                    )
                    game["teleporters"]["Impact Crater/Metroid Prime Lair/Teleporter to Credits"] = (
                        "End of Game/Credits"
                    )
                game["game"] = identify_game
                break


def _migrate_v7(json_dict: dict) -> None:
    renamed_items = {
        "3HP Life Capsule": "Small Life Capsule",
        "4HP Life Capsule": "Medium Life Capsule",
        "5HP Life Capsule": "Large Life Capsule",
        "Missile Expansion (24)": "Large Missile Expansion",
    }

    for game in json_dict["game_modifications"]:
        if game["game"] != "cave_story":
            continue
        for world, locations in game["locations"].items():
            game["locations"][world] = {k: renamed_items.get(v, v) for k, v in locations.items()}
        game["starting_items"]["Missiles"] = 5


def _migrate_v8(json_dict: dict) -> None:
    json_dict["info"]["randovania_version"] = json_dict["info"].pop("version")
    json_dict["info"]["randovania_version_git"] = "28492915"


def _migrate_v9(json_dict: dict) -> None:
    json_dict["info"]["has_spoiler"] = "game_modifications" in json_dict


def _migrate_v10(json_dict: dict) -> None:
    asset_id_conversion = {
        "prime2": {
            "1041207119": "Sanctuary Fortress/Sanctuary Energy Controller/Lore Scan",
            "1170414603": "Torvus Bog/Path of Roots/Lore Scan",
            "1238191924": "Torvus Bog/Gathering Hall/Lore Scan",
            "1394890590": "Agon Wastes/Mining Station A/Lore Scan",
            "1422425996": "Torvus Bog/Underground Tunnel/Lore Scan",
            "1489382579": "Torvus Bog/Torvus Lagoon/Keybearer Corpse (S-Dly)",
            "1657556419": "Sanctuary Fortress/Sanctuary Entrance/Keybearer Corpse (S-Jrs)",
            "1696621841": "Temple Grounds/Industrial Site/Keybearer Corpse (J-Fme)",
            "1764636206": "Agon Wastes/Portal Terminal/Lore Scan",
            "1948976790": "Sanctuary Fortress/Watch Station/Lore Scan",
            "2190580881": "Torvus Bog/Catacombs/Lore Scan",
            "2392838062": "Temple Grounds/Path of Eyes/Lore Scan",
            "2476408598": "Torvus Bog/Catacombs/Keybearer Corpse (G-Sch)",
            "2558035195": "Temple Grounds/Meeting Grounds/Lore Scan",
            "2677320745": "Torvus Bog/Training Chamber/Lore Scan",
            "2725438859": "Agon Wastes/Mining Station B/Lore Scan",
            "2844827238": "Sanctuary Fortress/Dynamo Works/Keybearer Corpse (C-Rch)",
            "3212301619": "Sanctuary Fortress/Main Research/Lore Scan",
            "3277287077": "Great Temple/Main Energy Controller/Lore Scan",
            "3478732186": "Temple Grounds/Fortress Transport Access/Lore Scan",
            "3529248034": "Torvus Bog/Torvus Energy Controller/Lore Scan",
            "353275320": "Agon Wastes/Central Mining Station/Keybearer Corpse (J-Stl)",
            "3729939997": "Agon Wastes/Main Reactor/Keybearer Corpse (B-Stl)",
            "3820230591": "Temple Grounds/Landing Site/Keybearer Corpse (M-Dhe)",
            "4021961856": "Agon Wastes/Agon Energy Controller/Lore Scan",
            "4072633400": "Sanctuary Fortress/Sanctuary Entrance/Lore Scan",
            "4115881194": "Sanctuary Fortress/Main Gyro Chamber/Lore Scan",
            "619091749": "Agon Wastes/Mining Plaza/Lore Scan",
            "67497535": "Sanctuary Fortress/Hall of Combat Mastery/Lore Scan",
            "686343194": "Temple Grounds/Storage Cavern A/Keybearer Corpse (D-Isl)",
            "971220893": "Temple Grounds/Transport to Agon Wastes/Lore Scan",
        },
        "cave_story": {
            "0": "Egg Corridor/Cthulhu's Abode/Hint - Cthulhu",
            "1": "Egg Corridor/Egg Corridor/Hint - Blue Robot",
            "10": "Sand Zone/Jenka's House/Hint - Jenka 2",
            "11": "Ruined Egg Corridor/Little House/Hint - Mrs. Little",
            "12": "Plantation/Statue Chamber/Hint - Numahachi 1",
            "13": "Plantation/Statue Chamber/Hint - Numahachi 2",
            "2": "Grasstown/Grasstown/Hint - Cthulhu (West)",
            "3": "Grasstown/Grasstown/Hint - Cthulhu (East)",
            "4": "Labyrinth/Labyrinth I/Hint - Blue Robot (Left)",
            "5": "Labyrinth/Labyrinth I/Hint - Blue Robot (Right)",
            "6": "Plantation/Plantation/Hint - Cthulhu",
            "7": "Ruined Egg Corridor/Egg Corridor?/Hint - Blue Robot",
            "8": "Grasstown/Power Room/Hint - MALCO",
            "9": "Sand Zone/Jenka's House/Hint - Jenka 1",
        },
    }

    for game in json_dict["game_modifications"]:
        game["hints"] = {asset_id_conversion[game["game"]][asset_id]: hint for asset_id, hint in game["hints"].items()}


def _migrate_v11(json_dict: dict) -> None:
    for game in json_dict["game_modifications"]:
        game["dock_weakness"] = {}
        if game["game"] == "dread" and json_dict["info"][0]["configuration"]["extra_pickups_for_bosses"]:
            game["locations"]["Cataris"]["Kraid Arena/Pickup (Kraid)"] = "Energy Transfer Module"


def _migrate_v12(json_dict: dict) -> None:
    for game in json_dict["game_modifications"]:
        if game["game"] == "dread":
            game["locations"].pop("Itorash")
            game["starting_items"].pop("Power Beam")
            game["starting_items"].pop("Power Suit")


def _migrate_v13(json_dict: dict) -> None:
    for game in json_dict["game_modifications"]:
        world_name, area_name = game["starting_location"].split("/", 1)
        node_name = migration_data.get_node_name_for_area(RandovaniaGame(game["game"]), world_name, area_name)
        game["starting_location"] = f"{game['starting_location']}/{node_name}"


def _migrate_v14(json_dict: dict) -> None:
    for game in json_dict["game_modifications"]:
        game["starting_equipment"] = {"items": game.pop("starting_items")}


def _migrate_v15(json_dict: dict) -> None:
    for game in json_dict["game_modifications"]:
        game["dock_connections"] = {}


def _migrate_v16(json_dict: dict) -> None:
    def _fix_node(name: str) -> str:
        return name.replace(
            "Navigation Room",
            "Save Station",
        )

    for game in json_dict["game_modifications"]:
        if game["game"] == "dread":
            game["hints"] = {_fix_node(node): hint for node, hint in game["hints"].items()}


def _migrate_v17(json_dict: dict) -> None:
    for game in json_dict["game_modifications"]:
        for hint in game["hints"].values():
            if (precision := hint.get("precision")) is not None:
                if precision["location"] == "relative-to-area":
                    old_loc = precision["relative"]["area_location"]
                    precision["relative"]["area_location"] = {
                        "region": old_loc["world_name"],
                        "area": old_loc["area_name"],
                    }
                elif precision["location"] == "world-only":
                    precision["location"] = "region-only"


def _migrate_v18(data: dict) -> None:
    for game in data["game_modifications"]:
        game_name = game["game"]
        if game_name in {"prime1", "prime2"}:
            default_node_per_area = migration_data.get_raw_data(RandovaniaGame(game_name))["default_node_per_area"]
            # remove teleporters and add to dock_connections
            for source, target in game["teleporters"].items():
                target_node = default_node_per_area[target]
                game["teleporters"][source] = f"{target}/{target_node}"

            game["dock_connections"].update(game.pop("teleporters"))
        else:
            game.pop("teleporters")


def _migrate_v19(data: dict) -> None:
    game_mod = data["game_modifications"]
    for game in game_mod:
        game_name = game["game"]
        if game_name in {"prime1", "prime2"}:
            mapping = migration_data.get_raw_data(RandovaniaGame(game_name))["rename_teleporter_nodes"]

            # starting location migration
            old_location = game["starting_location"]
            world_name, area_name, node_name = old_location.split("/", 2)
            new_node_name = mapping.get(old_location, None)
            if new_node_name is not None:
                game["starting_location"] = f"{world_name}/{area_name}/{new_node_name}"

            dock_connections = game["dock_connections"]
            dock_copy = dict(dock_connections.items())
            for id_from, id_to in dock_copy.items():
                world_name, area_name, node_name = id_from.split("/", 2)
                new_node_name_from = mapping.get(id_from, node_name)
                new_identifier_from = f"{world_name}/{area_name}/{new_node_name_from}"
                dock_connections[new_identifier_from] = dock_connections.pop(id_from)

                world_name, area_name, node_name = id_to.split("/", 2)
                new_node_name_to = mapping.get(id_to, node_name)
                new_identifier_to = f"{world_name}/{area_name}/{new_node_name_to}"
                dock_connections[new_identifier_from] = new_identifier_to

            if game_name in {"prime1", "prime2"}:
                mapping = migration_data.get_raw_data(RandovaniaGame(game_name))["dock_connection_fixes"]
                dock_connections = game["dock_connections"]
            for id_from, id_to in dock_connections.items():
                new_target = mapping.get(id_to, id_to)
                dock_connections[id_from] = new_target


def _migrate_v20(data: dict) -> None:
    game_modifications = data["game_modifications"]

    for game in game_modifications:
        game_name = game["game"]
        if game_name != "prime1":
            continue

        dock_weakness = game.get("dock_weakness")
        if dock_weakness is None:
            continue

        for weakness in dock_weakness.values():
            if weakness["name"] == "Charge Beam Door":
                weakness["name"] = "Charge Beam Blast Shield"
            elif weakness["name"] == "Bomb Door":
                weakness["name"] = "Bomb Blast Shield"


def _migrate_v21(data: dict) -> None:
    game_modifications = data["game_modifications"]

    for game in game_modifications:
        game_name = game["game"]
        if game_name != "dread":
            continue
        dock_weakness = game.get("dock_weakness")
        if dock_weakness is None:
            continue

        old_new_name = migration_data.get_raw_data(RandovaniaGame(game_name))["dairon_typo"]
        for old_name, new_name in old_new_name.items():
            if old_name in dock_weakness:
                dock_weakness[new_name] = dock_weakness.pop(old_name)


def _migrate_v22(data: dict) -> None:
    game_modifications = data["game_modifications"]

    for game in game_modifications:
        if "elevators" in game:
            game["teleporters"] = game.pop("elevators")


def _migrate_v23(data: dict) -> None:
    game_modifications = data["game_modifications"]

    for game in game_modifications:
        game_name = game["game"]
        if game_name != "am2r":
            continue

        migration = migration_data.get_raw_data(RandovaniaGame(game_name))["spazer_beam_typo"]

        dock_weakness = game.get("dock_weakness")
        if dock_weakness is not None:
            for old_node, new_node in migration["nodes"].items():
                if old_node in dock_weakness:
                    dock_weakness[new_node] = dock_weakness.pop(old_node)

        for region, area_data in migration["area"].items():
            for old_area_name, new_area_name in area_data.items():
                region_location = game["locations"][region]
                if old_area_name in region_location:
                    region_location[new_area_name] = region_location.pop(old_area_name)


def _migrate_v24(data: dict) -> None:
    game_modifications = data["game_modifications"]

    for game in game_modifications:
        game_name = game["game"]
        if game_name != "am2r":
            continue

        new_ammo_mapping = {
            "Missile Expansion": "Missile Tank",
            "Super Missile Expansion": "Super Missile Tank",
            "Power Bomb Expansion": "Power Bomb Tank",
        }

        game["starting_equipment"]["pickups"] = [
            new_ammo_mapping.get(pickup, pickup) for pickup in game["starting_equipment"]["pickups"]
        ]

        for area, locations in game["locations"].items():
            for node, item in locations.items():
                if item in new_ammo_mapping:
                    locations[node] = new_ammo_mapping[item]


def _migrate_v25(data: dict) -> None:
    is_mw_session = len(data["info"]["presets"]) > 1
    if not is_mw_session:
        return

    game_modifications = data["game_modifications"]
    all_am2r_players = [
        f"Player {index}"
        for index, preset in enumerate(data["info"]["presets"], start=1)
        if preset["schema_version"] >= 5 and preset["game"] == "am2r"
    ]
    player_re = r"^(.*) for (Player \d+)$"
    new_ammo_mapping = {
        "Missile Expansion": "Missile Tank",
        "Super Missile Expansion": "Super Missile Tank",
        "Power Bomb Expansion": "Power Bomb Tank",
    }

    for game in game_modifications:
        for area, locations in game["locations"].items():
            for node, item in locations.items():
                if item == "Energy Transfer Module":
                    continue
                match = re.match(player_re, item)
                assert match is not None
                item_name, player_name = match.group(1, 2)
                if player_name not in all_am2r_players:
                    continue
                if item_name in new_ammo_mapping:
                    locations[node] = f"{new_ammo_mapping[item_name]} for {player_name}"


def _migrate_v26(data: dict) -> None:
    for game in data["game_modifications"]:
        configurable_nodes: dict[str, dict] = game.pop("configurable_nodes")
        game["game_specific"] = {}

        if game["game"] != "prime2":
            continue

        def convert_to_enum(req: dict) -> str:
            non_scan = [name for it in req["data"]["items"] if (name := it["data"]["name"]) != "Scan"]
            if non_scan:
                return {
                    "Violet": "violet",
                    "Amber": "amber",
                    "Emerald": "emerald",
                    "Cobalt": "cobalt",
                }[non_scan[0]]
            else:
                return "removed"

        game["game_specific"]["translator_gates"] = {
            identifier: convert_to_enum(requirement) for identifier, requirement in configurable_nodes.items()
        }


def _migrate_v27(data: dict) -> None:
    game_modifications = data["game_modifications"]

    for game in game_modifications:
        game_name = game["game"]
        if game_name != "am2r":
            continue

        migration = migration_data.get_raw_data(RandovaniaGame(game_name))["a5_pipe_rename"]

        dock_connections = game.get("dock_connections")
        if dock_connections is not None and dock_connections != {}:
            for old_node, new_node in migration["nodes"].items():
                if old_node in dock_connections.keys():
                    dock_connections[new_node] = dock_connections.pop(old_node)
                for orig_connection, new_connection in dock_connections.items():
                    if old_node == new_connection:
                        dock_connections[orig_connection] = new_node

        dock_weakness = game.get("dock_weakness")
        if dock_weakness is not None and dock_weakness != {}:
            for old_name, new_name in migration["doors"].items():
                if old_name in dock_weakness.keys():
                    dock_weakness[new_name] = dock_weakness.pop(old_name)


def _migrate_v28(data: dict) -> None:
    game_modifications = data["game_modifications"]

    for game in game_modifications:
        game_name = game["game"]
        if game_name != "samus_returns":
            continue

        dock_weakness = game.get("dock_weakness")
        migration = migration_data.get_raw_data(RandovaniaGame(game_name))["a1_dlr_rename"]
        if dock_weakness is not None and dock_weakness != {}:
            for old_name, new_name in migration.items():
                if old_name in dock_weakness.keys():
                    dock_weakness[new_name] = dock_weakness.pop(old_name)


def _migrate_v29(data: dict) -> None:
    game_modifications = data["game_modifications"]

    for game in game_modifications:
        for hint in game["hints"].values():
            hint_type = hint["hint_type"]

            if hint_type != "red-temple-key-set":
                hint.pop("dark_temple", None)
            if hint_type != "location":
                hint.pop("precision", None)
                hint.pop("target", None)


def _migrate_hint_precision(data: dict, item_precisions_to_migrate: set[str]) -> None:
    game_modifications = data["game_modifications"]

    for game in game_modifications:
        game_enum = RandovaniaGame(game["game"])
        location_precision = migration_data.get_hint_location_precision_data(game_enum)

        for hint in game["hints"].values():
            if hint["hint_type"] != "location":
                continue

            precision = hint["precision"]
            if precision.get("location") in location_precision:
                precision["location_feature"] = location_precision[precision.pop("location")]

            def migrate_precision(_precision: dict, target: int, old_key: str, new_key: str) -> None:
                correct_name, area_and_node = migration_data.get_node_keys_for_pickup_index(game_enum, target)

                target_name = game["locations"][correct_name][area_and_node]
                target_name_re = re.compile(r"(.*) for Player (\d+)")

                if target_name == "Energy Transfer Module":
                    # who cares, honestly
                    _precision[old_key] = "detailed"
                    return

                pickup_name_match = target_name_re.match(target_name)
                if pickup_name_match is not None:
                    pickup_name = pickup_name_match.group(1)
                    target_player = int(pickup_name_match.group(2)) - 1
                else:
                    pickup_name = target_name
                    target_player = 0

                target_game = RandovaniaGame(game_modifications[target_player]["game"])
                old_categories = migration_data.get_old_hint_categories(target_game)

                if pickup_name in old_categories:
                    item_data = old_categories[pickup_name]
                else:
                    # generated pickups
                    item_data = next(data for name, data in old_categories.items() if pickup_name.startswith(name))

                _precision[new_key] = item_data[_precision.pop(old_key)]

            if precision.get("item") in item_precisions_to_migrate:
                migrate_precision(precision, hint["target"], "item", "item_feature")

            if (
                (relative := precision.get("relative")) is not None
                and ("area_location" not in relative)
                and (relative.get("precision") in item_precisions_to_migrate)
            ):
                migrate_precision(relative, relative["other_index"], "precision", "precision_feature")


def _migrate_v30(data: dict) -> None:
    _migrate_hint_precision(data, {"precise-category", "general-category"})


def _migrate_v31(data: dict) -> None:
    _migrate_hint_precision(data, {"broad-category"})


def _migrate_v32(data: dict) -> None:
    game_modifications = data["game_modifications"]

    for game in game_modifications:
        game_name = game["game"]
        if game_name != "samus_returns":
            continue

        migration = migration_data.get_raw_data(RandovaniaGame(game_name))["a4_crystal_mines_typo"]
        for region, area_data in migration["area"].items():
            for old_area_name, new_area_name in area_data.items():
                region_location = game["locations"][region]
                if old_area_name in region_location:
                    region_location[new_area_name] = region_location.pop(old_area_name)


def _migrate_v33(data: dict) -> None:
    game_modifications = data["game_modifications"]

    for game in game_modifications:
        if game["game"] == "prime2":
            banned_pickups = ["Cannon Ball", "Unlimited Beam Ammo", "Unlimited Missiles", "Double Damage"]
            if "pickups" in game["starting_equipment"]:
                starting_pickups = game["starting_equipment"]["pickups"]
                for pickup in banned_pickups:
                    if pickup in starting_pickups:
                        starting_pickups.remove(pickup)


_MIGRATIONS = [
    _migrate_v1,  # v2.2.0-6-gbfd37022
    _migrate_v2,  # v2.4.2-16-g735569fd
    _migrate_v3,  # v2.5.2-183-gbf62a4ef
    _migrate_v4,  # v3.2.1-40-g94ed9301
    _migrate_v5,  # v3.2.1-203-g6e303090
    _migrate_v6,
    _migrate_v7,  # v3.3.0dev721
    _migrate_v8,
    _migrate_v9,
    _migrate_v10,
    _migrate_v11,
    _migrate_v12,
    _migrate_v13,
    _migrate_v14,
    _migrate_v15,
    _migrate_v16,
    _migrate_v17,
    _migrate_v18,
    _migrate_v19,
    _migrate_v20,
    _migrate_v21,
    _migrate_v22,
    _migrate_v23,
    _migrate_v24,  # AM2R expansion -> tank rename for solo games
    _migrate_v25,  # AM2R expansion -> tank rename for MW games
    _migrate_v26,  # configurable nodes -> game_specific
    _migrate_v27,
    _migrate_v28,
    _migrate_v29,  # hint type refactor
    _migrate_v30,  # migrate some HintLocationPrecision and HintItemPrecision to HintFeature
    _migrate_v31,  # remove HintLocationPrecision.BROAD_CATEGORY
    _migrate_v32,  # MSR Rename Area 4 Crystal Mines - Gamma Arena to Gamma+ Arena
    _migrate_v33,
]
CURRENT_VERSION = migration_lib.get_version(_MIGRATIONS)


def convert_to_current_version(json_dict: dict) -> dict:
    return migration_lib.apply_migrations(
        json_dict,
        _MIGRATIONS,
        version_name="rdvgame version",
    )
