import math
import uuid
from typing import Dict

from randovania.game_description import migration_data, default_database
from randovania.games.game import RandovaniaGame
from randovania.lib import migration_lib

CURRENT_VERSION = 32


def _migrate_v1(preset: dict) -> dict:
    layout_configuration = preset["layout_configuration"]
    layout_configuration["beam_configuration"] = {
        "power": {
            "item_index": 0,
            "ammo_a": -1,
            "ammo_b": -1,
            "uncharged_cost": 0,
            "charged_cost": 0,
            "combo_missile_cost": 5,
            "combo_ammo_cost": 0
        },
        "dark": {
            "item_index": 1,
            "ammo_a": 45,
            "ammo_b": -1,
            "uncharged_cost": 1,
            "charged_cost": 5,
            "combo_missile_cost": 5,
            "combo_ammo_cost": 30
        },
        "light": {
            "item_index": 2,
            "ammo_a": 46,
            "ammo_b": -1,
            "uncharged_cost": 1,
            "charged_cost": 5,
            "combo_missile_cost": 5,
            "combo_ammo_cost": 30
        },
        "annihilator": {
            "item_index": 3,
            "ammo_a": 46,
            "ammo_b": 45,
            "uncharged_cost": 1,
            "charged_cost": 5,
            "combo_missile_cost": 5,
            "combo_ammo_cost": 30
        }
    }
    layout_configuration["skip_final_bosses"] = False
    layout_configuration["energy_per_tank"] = 100
    return preset


def _migrate_v2(preset: dict) -> dict:
    level_renaming = {
        "trivial": "beginner",
        "easy": "intermediate",
        "normal": "advanced",
        "hard": "expert",
        "minimal-restrictions": "minimal-logic",
    }
    trick_level = preset["layout_configuration"]["trick_level"]
    trick_level["global_level"] = level_renaming.get(trick_level["global_level"], trick_level["global_level"])
    for specific, value in trick_level["specific_levels"].items():
        trick_level["specific_levels"][specific] = level_renaming.get(value, value)

    return preset


def _migrate_v3(preset: dict) -> dict:
    preset["layout_configuration"]["safe_zone"] = {
        "fully_heal": True,
        "prevents_dark_aether": True,
        "heal_per_second": 1.0,
    }
    return preset


def _migrate_v4(preset: dict) -> dict:
    trick_name_mapping = {
        0: "Dash",
        1: "BombJump",
        2: "SlopeJump",
        3: "Movement",
        4: "BSJ",
        5: "RollJump",
        6: "UnderwaterDash",
        7: "AirUnderwater",
        8: "OoB",
        10: "SAnoSJ",
        11: "WallBoost",
        12: "EnemyHop",
        13: "Combat",
        15: "InstantMorph",
        26: "InvisibleObjects",
        27: "StandableTerrain",
        28: "TerminalFall",
        29: "BoostJump",
        30: "EDash",
        31: "BomblessSlot",
        32: "ScanPost",
        33: "ScrewAttackTunnels",
        34: "Knowledge",
        35: "SeekerlessLocks",
    }

    preset["layout_configuration"]["game"] = "prime2"

    trick_level = preset["layout_configuration"]["trick_level"]
    global_level = trick_level.pop("global_level")

    trick_level["minimal_logic"] = global_level == "minimal-logic"
    specific_levels = {
        trick_name_mapping[int(index)]: level
        for index, level in trick_level["specific_levels"].items()
    }
    if global_level == "minimal-logic":
        specific_levels = {}
    elif global_level == "beginner":
        for trick in ["BombJump", "Knowledge", "Movement", "ScanPost", "SAnoSJ"]:
            specific_levels[trick] = "beginner"
    else:
        for trick in trick_name_mapping.values():
            if trick not in specific_levels:
                specific_levels[trick] = global_level

    trick_level["specific_levels"] = specific_levels

    return preset


def _migrate_v5(preset: dict) -> dict:
    excluded_item = {
        "include_copy_in_original_location": False,
        "num_shuffled_pickups": 0,
        "num_included_in_starting_items": 0,
        "included_ammo": [],
        "allowed_as_random_starting_item": True,
    }
    included_item = {
        **excluded_item,
        "num_included_in_starting_items": 1
    }
    shuffled_item = {
        **excluded_item,
        "num_shuffled_pickups": 1,
    }

    default_items_state = {
        "Progressive Suit": {**excluded_item, "num_shuffled_pickups": 2},
        "Dark Beam": {**shuffled_item, "included_ammo": [50]},
        "Light Beam": {**shuffled_item, "included_ammo": [50]},
        "Annihilator Beam": {**shuffled_item, "included_ammo": [0, 0]},
        "Power Bomb": {**shuffled_item, "included_ammo": [2]},
        "Progressive Grapple": {**excluded_item, "num_shuffled_pickups": 2},
        "Missile Launcher": {**shuffled_item, "included_ammo": [5]},
        "Seeker Launcher": {**shuffled_item, "included_ammo": [5]},
        "Energy Tank": {**excluded_item, "num_shuffled_pickups": 14},
    }

    for item in ["Combat Visor", "Scan Visor", "Varia Suit", "Power Beam", "Charge Beam", "Morph Ball"]:
        default_items_state[item] = included_item
    for item in ["Dark Visor", "Echo Visor", "Morph Ball Bomb", "Boost Ball", "Spider Ball", "Space Jump Boots",
                 "Gravity Boost", "Super Missile", "Sunburst", "Darkburst", "Sonic Boom", "Violet Translator",
                 "Amber Translator", "Emerald Translator", "Cobalt Translator"]:
        default_items_state[item] = shuffled_item

    major_items = preset["layout_configuration"]["major_items_configuration"]["items_state"]
    for item in default_items_state.keys():
        if item not in major_items:
            major_items[item] = default_items_state[item]

    preset["layout_configuration"]["major_items_configuration"].pop("progressive_suit")
    preset["layout_configuration"]["major_items_configuration"].pop("progressive_grapple")
    preset["layout_configuration"].pop("split_beam_ammo")

    specific_levels: Dict[str, str] = preset["layout_configuration"]["trick_level"]["specific_levels"]
    tricks_to_remove = [trick_name for trick_name, level in specific_levels.items() if level == "no-tricks"]
    for trick in tricks_to_remove:
        specific_levels.pop(trick)

    preset["game"] = preset["layout_configuration"].pop("game")
    preset["configuration"] = preset.pop("layout_configuration")
    preset["configuration"].update(preset.pop("patcher_configuration"))
    preset["configuration"]["varia_suit_damage"] = max(preset["configuration"]["varia_suit_damage"], 0.1)

    return preset


def _migrate_v6(preset: dict) -> dict:
    preset["configuration"]["dangerous_energy_tank"] = False
    return preset


def _migrate_v7(preset: dict) -> dict:
    default_items = {}
    if preset["game"] == "prime2":
        default_items["visor"] = "Combat Visor"
        default_items["beam"] = "Power Beam"

    preset["configuration"]["major_items_configuration"]["default_items"] = default_items
    return preset


def _migrate_v8(preset: dict) -> dict:
    game = default_database.game_description_for(RandovaniaGame(preset["game"]))

    # FIXME: area location is now something different, this code broke

    def _name_to_location(name: str):
        world_name, area_name = name.split("/", 1)
        world = game.world_list.world_with_name(world_name)
        area = world.area_by_name(area_name)
        return {
            "world_asset_id": world.extra["asset_id"],
            "area_asset_id": area.extra["asset_id"],
        }

    preset["configuration"]["multi_pickup_placement"] = False

    if "energy_per_tank" in preset["configuration"]:
        preset["configuration"]["energy_per_tank"] = int(preset["configuration"]["energy_per_tank"])

    preset["configuration"]["starting_location"] = [
        _name_to_location(location)
        for location in preset["configuration"]["starting_location"]
    ]

    excluded_teleporters = []
    if preset["game"] == "prime2":
        excluded_teleporters = [
            {
                "world_asset_id": 464164546,
                "area_asset_id": 3136899603,
                "instance_id": 204865660
            },
            {
                "world_asset_id": 2252328306,
                "area_asset_id": 2068511343,
                "instance_id": 589949
            },
            {
                "world_asset_id": 464164546,
                "area_asset_id": 1564082177,
                "instance_id": 4260106
            },
            {
                "world_asset_id": 1006255871,
                "area_asset_id": 2278776548,
                "instance_id": 136970379
            },
        ]

    preset["configuration"]["elevators"] = {
        "mode": preset["configuration"]["elevators"],
        "excluded_teleporters": excluded_teleporters,
        "excluded_targets": [],
        "skip_final_bosses": preset["configuration"].pop("skip_final_bosses", False),
        "allow_unvisited_room_names": True,
    }
    if preset["configuration"]["major_items_configuration"]["default_items"].get("visor") == "Dark Visor":
        preset["configuration"]["major_items_configuration"]["default_items"]["visor"] = "Combat Visor"
        preset["configuration"]["major_items_configuration"]["items_state"]["Scan Visor"] = {
            "num_included_in_starting_items": 1
        }

    return preset


def _migrate_v9(preset: dict) -> dict:
    if preset.get("uuid") is None:
        preset["uuid"] = str(uuid.uuid4())

    _name_to_uuid = {
        "Corruption Preset": "5682c9ef-d447-4327-b473-ba1216d83439",
        "Darkszero's Deluxe": "ea1eced4-53b8-4bb3-a08f-27ac1afe6aab",
        "Fewest Changes": "bba48268-0710-4ac5-baae-dcd5fcd31d80",
        "Prime Preset": "e36f52b3-ccd9-4dd7-a18f-b57b25f6b079",
        "Starter Preset": "fcbe4e3f-b1fa-41cc-83cb-c86d84c10f0f",
    }

    base_preset_name = preset.pop("base_preset_name")
    preset["base_preset_uuid"] = _name_to_uuid.get(base_preset_name, str(uuid.uuid4()))

    if preset["game"] != "prime2":
        preset["configuration"].pop("dangerous_energy_tank")

    return preset


def _migrate_v10(preset: dict) -> dict:
    if preset["game"] == "prime1":
        major = preset["configuration"].pop("qol_major_cutscenes")
        minor = preset["configuration"].pop("qol_minor_cutscenes")
        if major:
            cutscenes = "major"
        elif minor:
            cutscenes = "minor"
        else:
            cutscenes = "original"
        preset["configuration"]["qol_cutscenes"] = cutscenes

    elif preset["game"] == "prime2":
        preset["configuration"]["allow_jumping_on_dark_water"] = False
        fields = [
            "allow_vanilla_dark_beam",
            "allow_vanilla_light_beam",
            "allow_vanilla_seeker_launcher",
            "allow_vanilla_echo_visor",
            "allow_vanilla_dark_visor",
            "allow_vanilla_screw_attack",
            "allow_vanilla_gravity_boost",
            "allow_vanilla_boost_ball",
            "allow_vanilla_spider_ball",
        ]
        for f in fields:
            preset["configuration"][f] = True

    return preset


def _migrate_v11(preset: dict) -> dict:
    if preset["game"] == "prime1":
        preset["configuration"]["warp_to_start"] = False

    return preset


def _migrate_v12(preset: dict) -> dict:
    preset["configuration"]["logical_resource_action"] = "randomly"
    if preset["game"] == "prime1":
        preset["configuration"]["artifact_target"] = preset["configuration"].pop("artifacts")
        preset["configuration"]["artifact_minimum_progression"] = 0
        preset["configuration"]["qol_pickup_scans"] = False

    return preset


def _migrate_v13(preset: dict) -> dict:
    for config in preset["configuration"]["major_items_configuration"]["items_state"].values():
        config.pop("allowed_as_random_starting_item", None)

    maximum_ammo = preset["configuration"]["ammo_configuration"].pop("maximum_ammo")
    ammo_ids = {
        "prime1": {
            "Missile Expansion": ["4"],
            "Power Bomb Expansion": ["7"],
        },
        "prime2": {
            "Missile Expansion": ["44"],
            "Power Bomb Expansion": ["43"],
            "Dark Ammo Expansion": ["45"],
            "Light Ammo Expansion": ["46"],
            "Beam Ammo Expansion": ["45", "46"],
        },
        "prime3": {
            "Missile Expansion": ["4"],
            "Ship Missile Expansion": ["45"],
        },
        "super_metroid": {
            "Missile Expansion": ["5"],
            "Super Missile Expansion": ["6"],
            "Power Bomb Expansion": ["7"],
        },
    }[preset["game"]]
    main_items = {
        "prime1": {
            "Missile Launcher": ["4"],
            "Power Bomb": ["7"],
        },
        "prime2": {
            "Dark Beam": ["45"],
            "Light Beam": ["46"],
            "Annihilator Beam": ["45", "46"],
            "Missile Launcher": ["44"],
            "Seeker Launcher": ["44"],
            "Power Bomb": ["43"],
        },
        "prime3": {
            "Missile Launcher": ["4"],
            "Ship Missile": ["45"],
        },
        "super_metroid": {},
    }

    for item, ids in main_items[preset["game"]].items():
        item_state = preset["configuration"]["major_items_configuration"]["items_state"][item]
        count = item_state.get("num_shuffled_pickups", 0) + item_state.get("num_included_in_starting_items", 0)
        if item_state.get("include_copy_in_original_location", False):
            count += 1

        for ammo_id, ammo in zip(ids, item_state["included_ammo"]):
            maximum_ammo[ammo_id] -= ammo * count

    for name, config in preset["configuration"]["ammo_configuration"]["items_state"].items():
        config["ammo_count"] = [
            math.ceil(max(maximum_ammo[ammo_id], 0) / max(config["pickup_count"], 1))
            for ammo_id in ammo_ids[name]
        ]
        config.pop("variance")

    return preset


def _migrate_v14(preset: dict) -> dict:
    game = RandovaniaGame(preset["game"])
    db = default_database.game_description_for(game)

    def _migrate_area_location(old_loc: dict[str, int]) -> dict[str, str]:
        result = migration_data.convert_area_loc_id_to_name(game, old_loc)

        if "instance_id" in old_loc:
            # FIXME
            world = db.world_list.world_with_name(result["world_name"])
            area = world.area_by_name(result["area_name"])
            for node in area.nodes:
                if node.extra.get("teleporter_instance_id") == old_loc["instance_id"]:
                    result["node_name"] = node.name
                    break

        return result

    preset["configuration"]["starting_location"] = [
        _migrate_area_location(old_loc)
        for old_loc in preset["configuration"]["starting_location"]
    ]

    if "elevators" in preset["configuration"]:
        elevators = preset["configuration"]["elevators"]

        elevators["excluded_teleporters"] = [
            _migrate_area_location(old_loc)
            for old_loc in elevators["excluded_teleporters"]
        ]
        elevators["excluded_targets"] = [
            _migrate_area_location(old_loc)
            for old_loc in elevators["excluded_targets"]
        ]

        preset["configuration"]["elevators"] = elevators

    return preset


def _migrate_v15(preset: dict) -> dict:
    gate_mapping = {'Temple Grounds/Hive Access Tunnel/Translator Gate': 0,
                    'Temple Grounds/Meeting Grounds/Translator Gate': 1,
                    'Temple Grounds/Hive Transport Area/Translator Gate': 2,
                    'Temple Grounds/Industrial Site/Translator Gate': 3,
                    'Temple Grounds/Path of Eyes/Translator Gate': 4,
                    'Temple Grounds/Temple Assembly Site/Translator Gate': 5,
                    'Temple Grounds/GFMC Compound/Translator Gate': 6,
                    'Great Temple/Temple Sanctuary/Transport A Translator Gate': 9,
                    'Great Temple/Temple Sanctuary/Transport B Translator Gate': 7,
                    'Great Temple/Temple Sanctuary/Transport C Translator Gate': 8,
                    'Agon Wastes/Mining Plaza/Translator Gate': 10,
                    'Agon Wastes/Mining Station A/Translator Gate': 11,
                    'Torvus Bog/Great Bridge/Translator Gate': 12,
                    'Torvus Bog/Torvus Temple/Translator Gate': 13,
                    'Torvus Bog/Torvus Temple/Elevator Translator Scan': 14,
                    'Sanctuary Fortress/Reactor Core/Translator Gate': 15,
                    'Sanctuary Fortress/Sanctuary Temple/Translator Gate': 16}

    if preset["game"] == "prime2":
        translator_configuration = preset["configuration"]["translator_configuration"]
        old = translator_configuration["translator_requirement"]
        translator_configuration["translator_requirement"] = {
            identifier: old[str(gate_index)]
            for identifier, gate_index in gate_mapping.items()
        }

    return preset


def _migrate_v16(preset: dict) -> dict:
    if preset["game"] == "prime1":
        art_hints = {"artifacts": "precise"}
        preset["configuration"]["hints"] = art_hints

    return preset


def _migrate_v17(preset: dict) -> dict:
    if preset["game"] == "prime1":
        preset["configuration"]["elevators"]["excluded_teleporters"].append(
            {
                "world_name": "Impact Crater",
                "area_name": "Metroid Prime Lair",
                "node_name": "Teleporter to Credits"
            }
        )
        preset["configuration"]["elevators"]["excluded_teleporters"].append(
            {
                "world_name": "Frigate Orpheon",
                "area_name": "Exterior Docking Hangar",
                "node_name": "Teleport to Landing Site"
            }
        )
    return preset


def _migrate_v18(preset: dict) -> dict:
    if preset["game"] == "prime1":
        preset["configuration"]["shuffle_item_pos"] = False
        preset["configuration"]["items_every_room"] = False
    return preset


def _migrate_v19(preset: dict) -> dict:
    if preset["game"] == "cave_story":
        itemconfig = preset["configuration"]["major_items_configuration"]["items_state"]
        ammoconfig = preset["configuration"]["ammo_configuration"]["items_state"]

        if itemconfig.get("Base Missiles") is not None:
            # handles presets which were hand-migrated before this func was written
            return preset

        itemconfig["Base Missiles"] = {
            "num_included_in_starting_items": 1,
            "included_ammo": [5],
        }

        itemconfig["Missile Launcher"].pop("included_ammo", None)
        itemconfig["Super Missile Launcher"].pop("included_ammo", None)
        itemconfig["Progressive Missile Launcher"].pop("included_ammo", None)

        itemconfig["Small Life Capsule"] = itemconfig.pop("3HP Life Capsule")
        itemconfig["Medium Life Capsule"] = itemconfig.pop("4HP Life Capsule")
        itemconfig["Large Life Capsule"] = itemconfig.pop("5HP Life Capsule")

        ammoconfig["Large Missile Expansion"] = ammoconfig.pop("Missile Expansion (24)")

        preset["configuration"]["major_items_configuration"]["items_state"] = itemconfig
        preset["configuration"]["ammo_configuration"]["items_state"] = ammoconfig

    return preset


def _migrate_v20(preset: dict) -> dict:
    if preset["game"] == "prime1":
        preset["configuration"]["spring_ball"] = False

    return preset


def _migrate_v21(preset: dict) -> dict:
    if preset["game"] == "prime1":
        preset["configuration"]["deterministic_idrone"] = True

    return preset


def _migrate_v22(preset: dict) -> dict:
    if preset["game"] == "dread":
        preset["configuration"].pop("disable_adam_convos")

    return preset


def _migrate_v23(preset: dict) -> dict:
    preset["configuration"]["first_progression_must_be_local"] = False

    return preset


def _migrate_v24(preset: dict) -> dict:
    if preset["game"] == "prime1":
        preset["configuration"]["deterministic_maze"] = True

    return preset


def _migrate_v25(preset: dict) -> dict:
    if preset["game"] == "prime1":
        preset["configuration"]["random_boss_sizes"] = False
        preset["configuration"]["no_doors"] = False
        preset["configuration"]["superheated_probability"] = 0
        preset["configuration"]["submerged_probability"] = 0
        preset["configuration"]["room_rando"] = "None"
        preset["configuration"]["large_samus"] = False

    return preset


def _migrate_v26(preset: dict) -> dict:
    preset["configuration"]["minimum_available_locations_for_hint_placement"] = 0
    preset["configuration"]["minimum_location_weight_for_hint_placement"] = 0.0
    if preset["game"] == "dread":
        preset["configuration"]["immediate_energy_parts"] = True
    return preset


def _migrate_v27(preset: dict) -> dict:
    if preset["game"] == "prime1" and "phazon_suit" not in preset["configuration"]["hints"].keys():
        preset["configuration"]["hints"]["phazon_suit"] = "hide-area"
    return preset


def _migrate_v28(preset: dict) -> dict:
    if preset["game"] == "dread":
        for config in ["hanubia_shortcut_no_grapple", "hanubia_easier_path_to_itorash", "extra_pickups_for_bosses"]:
            preset["configuration"][config] = True

    return preset


def _migrate_v29(preset: dict) -> dict:
    if preset["game"] == "dread":
        preset["configuration"]["x_starts_released"] = False

    return preset


def _migrate_v30(preset: dict) -> dict:
    if preset["game"] == "dread":
        for item in ("Metroid Suit", "Hyper Beam", "Power Suit", "Power Beam"):
            preset["configuration"]["major_items_configuration"]["items_state"].pop(item)

    return preset


def _migrate_v31(preset: dict) -> dict:
    preset["configuration"]["multi_pickup_new_weighting"] = False

    return preset


_MIGRATIONS = {
    1: _migrate_v1,  # v1.1.1-247-gaf9e4a69
    2: _migrate_v2,  # v1.2.2-71-g0fbabe91
    3: _migrate_v3,  # v1.2.2-563-g50f4d07a
    4: _migrate_v4,  # v1.2.2-832-gec9b8004
    5: _migrate_v5,  # v2.0.2-15-g1096103d
    6: _migrate_v6,  # v2.1.2-61-g8bb33489
    7: _migrate_v7,  # v2.3.0-27-g6b4168b8
    8: _migrate_v8,  # v2.5.2-39-g3cf0b27d
    9: _migrate_v9,  # v2.6.1-33-gf0b8ec32
    10: _migrate_v10,  # v2.6.1-416-g358711ce
    11: _migrate_v11,  # v2.6.1-494-g086eb8cf
    12: _migrate_v12,  # v3.0.2-13-gdffb4b9a
    13: _migrate_v13,  # v3.1.3-122-g9f50c418
    14: _migrate_v14,  # v3.2.1-44-g11823eac
    15: _migrate_v15,  # v3.2.1-203-g6e303090
    16: _migrate_v16,  # v3.2.1-363-g3a93b533
    17: _migrate_v17,
    18: _migrate_v18,
    19: _migrate_v19,  # v3.3.0dev721
    20: _migrate_v20,
    21: _migrate_v21,
    22: _migrate_v22,
    23: _migrate_v23,
    24: _migrate_v24,
    25: _migrate_v25,
    26: _migrate_v26,
    27: _migrate_v27,
    28: _migrate_v28,
    29: _migrate_v29,
    30: _migrate_v30,
    31: _migrate_v31,
}


def convert_to_current_version(preset: dict) -> dict:
    return migration_lib.migrate_to_version(
        preset,
        CURRENT_VERSION,
        _MIGRATIONS,
    )
