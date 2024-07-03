from __future__ import annotations

import copy
import math
import uuid

from randovania.game_description import migration_data
from randovania.games.game import RandovaniaGame
from randovania.lib import migration_lib


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
            "combo_ammo_cost": 0,
        },
        "dark": {
            "item_index": 1,
            "ammo_a": 45,
            "ammo_b": -1,
            "uncharged_cost": 1,
            "charged_cost": 5,
            "combo_missile_cost": 5,
            "combo_ammo_cost": 30,
        },
        "light": {
            "item_index": 2,
            "ammo_a": 46,
            "ammo_b": -1,
            "uncharged_cost": 1,
            "charged_cost": 5,
            "combo_missile_cost": 5,
            "combo_ammo_cost": 30,
        },
        "annihilator": {
            "item_index": 3,
            "ammo_a": 46,
            "ammo_b": 45,
            "uncharged_cost": 1,
            "charged_cost": 5,
            "combo_missile_cost": 5,
            "combo_ammo_cost": 30,
        },
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
    specific_levels = {trick_name_mapping[int(index)]: level for index, level in trick_level["specific_levels"].items()}
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
    included_item = {**excluded_item, "num_included_in_starting_items": 1}
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
    for item in [
        "Dark Visor",
        "Echo Visor",
        "Morph Ball Bomb",
        "Boost Ball",
        "Spider Ball",
        "Space Jump Boots",
        "Gravity Boost",
        "Super Missile",
        "Sunburst",
        "Darkburst",
        "Sonic Boom",
        "Violet Translator",
        "Amber Translator",
        "Emerald Translator",
        "Cobalt Translator",
    ]:
        default_items_state[item] = shuffled_item

    major_items = preset["layout_configuration"]["major_items_configuration"]["items_state"]
    for item in default_items_state.keys():
        if item not in major_items:
            major_items[item] = default_items_state[item]

    preset["layout_configuration"]["major_items_configuration"].pop("progressive_suit")
    preset["layout_configuration"]["major_items_configuration"].pop("progressive_grapple")
    preset["layout_configuration"].pop("split_beam_ammo")

    specific_levels: dict[str, str] = preset["layout_configuration"]["trick_level"]["specific_levels"]
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
    migration = migration_data.get_raw_data(RandovaniaGame(preset["game"]))

    def _name_to_location(name: str):
        world_name, area_name = name.split("/", 1)
        return {
            "world_asset_id": migration["world_name_to_id"][world_name],
            "area_asset_id": migration["area_name_to_id"][world_name][area_name],
        }

    preset["configuration"]["multi_pickup_placement"] = False

    if "energy_per_tank" in preset["configuration"]:
        preset["configuration"]["energy_per_tank"] = int(preset["configuration"]["energy_per_tank"])

    preset["configuration"]["starting_location"] = [
        _name_to_location(location) for location in preset["configuration"]["starting_location"]
    ]

    excluded_teleporters = []
    if preset["game"] == "prime2":
        excluded_teleporters = [
            {"world_asset_id": 464164546, "area_asset_id": 3136899603, "instance_id": 204865660},
            {"world_asset_id": 2252328306, "area_asset_id": 2068511343, "instance_id": 589949},
            {"world_asset_id": 464164546, "area_asset_id": 1564082177, "instance_id": 4260106},
            {"world_asset_id": 1006255871, "area_asset_id": 2278776548, "instance_id": 136970379},
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
            math.ceil(max(maximum_ammo[ammo_id], 0) / max(config["pickup_count"], 1)) for ammo_id in ammo_ids[name]
        ]
        config.pop("variance")

    return preset


def _migrate_v14(preset: dict) -> dict:
    game = RandovaniaGame(preset["game"])

    def _migrate_area_location(old_loc: dict[str, int]) -> dict[str, str]:
        return migration_data.convert_area_loc_id_to_name(game, old_loc)

    preset["configuration"]["starting_location"] = [
        _migrate_area_location(old_loc) for old_loc in preset["configuration"]["starting_location"]
    ]

    if "elevators" in preset["configuration"]:
        elevators = preset["configuration"]["elevators"]

        elevators["excluded_teleporters"] = [
            _migrate_area_location(old_loc) for old_loc in elevators["excluded_teleporters"]
        ]
        elevators["excluded_targets"] = [_migrate_area_location(old_loc) for old_loc in elevators["excluded_targets"]]

        preset["configuration"]["elevators"] = elevators

    return preset


def _migrate_v15(preset: dict) -> dict:
    gate_mapping = {
        "Temple Grounds/Hive Access Tunnel/Translator Gate": 0,
        "Temple Grounds/Meeting Grounds/Translator Gate": 1,
        "Temple Grounds/Hive Transport Area/Translator Gate": 2,
        "Temple Grounds/Industrial Site/Translator Gate": 3,
        "Temple Grounds/Path of Eyes/Translator Gate": 4,
        "Temple Grounds/Temple Assembly Site/Translator Gate": 5,
        "Temple Grounds/GFMC Compound/Translator Gate": 6,
        "Great Temple/Temple Sanctuary/Transport A Translator Gate": 9,
        "Great Temple/Temple Sanctuary/Transport B Translator Gate": 7,
        "Great Temple/Temple Sanctuary/Transport C Translator Gate": 8,
        "Agon Wastes/Mining Plaza/Translator Gate": 10,
        "Agon Wastes/Mining Station A/Translator Gate": 11,
        "Torvus Bog/Great Bridge/Translator Gate": 12,
        "Torvus Bog/Torvus Temple/Translator Gate": 13,
        "Torvus Bog/Torvus Temple/Elevator Translator Scan": 14,
        "Sanctuary Fortress/Reactor Core/Translator Gate": 15,
        "Sanctuary Fortress/Sanctuary Temple/Translator Gate": 16,
    }

    if preset["game"] == "prime2":
        translator_configuration = preset["configuration"]["translator_configuration"]
        old = translator_configuration["translator_requirement"]
        translator_configuration["translator_requirement"] = {
            identifier: old[str(gate_index)] for identifier, gate_index in gate_mapping.items()
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
            {"world_name": "Impact Crater", "area_name": "Metroid Prime Lair", "node_name": "Teleporter to Credits"}
        )
        preset["configuration"]["elevators"]["excluded_teleporters"].append(
            {
                "world_name": "Frigate Orpheon",
                "area_name": "Exterior Docking Hangar",
                "node_name": "Teleport to Landing Site",
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


def _update_default_dock_rando_for_game(preset: dict, game: RandovaniaGame) -> dict:
    if preset["game"] == game.value:
        preset["configuration"]["dock_rando"] = {
            "mode": "vanilla",
            "types_state": copy.deepcopy(migration_data.get_default_dock_lock_settings(game)),
        }
    return preset


def _update_default_dock_rando(preset: dict) -> dict:
    game = RandovaniaGame(preset["game"])
    return _update_default_dock_rando_for_game(preset, game)


def _migrate_v32(preset: dict) -> dict:
    return _update_default_dock_rando(preset)


def _migrate_v33(preset: dict) -> dict:
    if preset["game"] == "dread":
        preset["configuration"].pop("extra_pickups_for_bosses")
        preset["configuration"]["artifacts"] = {
            "prefer_emmi": True,
            "prefer_major_bosses": True,
            "required_artifacts": 0,
        }

    return preset


def _migrate_v34(preset: dict) -> dict:
    preset["configuration"].pop("multi_pickup_placement")
    preset["configuration"].pop("multi_pickup_new_weighting")

    return preset


def _migrate_v35(preset: dict) -> dict:
    if preset["game"] == "dread":
        preset["configuration"]["linear_damage_runs"] = False
        preset["configuration"]["linear_dps"] = 20
    return preset


def _migrate_v36(preset: dict) -> dict:
    if preset["game"] == "prime1":
        preset["configuration"]["enemy_attributes"] = None
    return preset


def _migrate_v37(preset: dict) -> dict:
    if preset["game"] == "dread":
        config = preset["configuration"]
        damage = config.pop("linear_dps")
        if not config.pop("linear_damage_runs"):
            damage = None
        config["constant_heat_damage"] = config["constant_cold_damage"] = config["constant_lava_damage"] = damage

    return preset


def _migrate_v38(preset: dict) -> dict:
    # New version since we don't write the base_preset_uuid to the preset itself anymore
    # But leave it there to migrate easily to options
    return preset


def _migrate_v39(preset: dict) -> dict:
    if preset["game"] == "dread":
        preset["configuration"]["allow_highly_dangerous_logic"] = False

    return preset


def _migrate_v40(preset: dict) -> dict:
    if preset["game"] == "prime1":
        preset["configuration"]["blue_save_doors"] = False
    return preset


def _migrate_v41(preset: dict) -> dict:
    if preset["game"] == "prime2":
        preset["configuration"]["use_new_patcher"] = False
        preset["configuration"]["inverted_mode"] = False

    return preset


def _migrate_v42(preset: dict) -> dict:
    if preset["game"] == "dread":
        preset = _update_default_dock_rando(preset)
    return preset


def _migrate_v43(preset: dict) -> dict:
    preset["configuration"]["single_set_for_pickups_that_solve"] = False
    preset["configuration"]["staggered_multi_pickup_placement"] = False
    return preset


def _migrate_v44(preset: dict) -> dict:
    def add_node_name(location):
        node_name = migration_data.get_node_name_for_area(preset["game"], location["world_name"], location["area_name"])
        location["node_name"] = node_name

    for loc in preset["configuration"]["starting_location"]:
        add_node_name(loc)

    if "elevators" in preset["configuration"]:
        result = []
        for loc in preset["configuration"]["elevators"]["excluded_teleporters"]:
            try:
                add_node_name(loc)
                result.append(loc)
            except KeyError:
                continue
        preset["configuration"]["elevators"]["excluded_teleporters"] = result

        for loc in preset["configuration"]["elevators"]["excluded_targets"]:
            add_node_name(loc)

    return preset


def _migrate_v45(preset: dict) -> dict:
    if preset["game"] == "prime2":
        preset["configuration"]["portal_rando"] = False
    return preset


def _migrate_v46(preset: dict) -> dict:
    if preset["game"] == "dread":
        preset["configuration"]["april_fools_hints"] = False
    return preset


def _migrate_v47(preset: dict) -> dict:
    if preset["game"] == "prime1":
        preset["configuration"].pop("deterministic_idrone")
        preset["configuration"].pop("deterministic_maze")
        preset["configuration"].pop("qol_game_breaking")
        preset["configuration"].pop("qol_pickup_scans")
        preset["configuration"].pop("heat_protection_only_varia")
        preset["configuration"]["legacy_mode"] = False
    return preset


def _migrate_v48(preset: dict) -> dict:
    ammo_pickup_config = preset["configuration"].pop("ammo_configuration")
    ammo_pickup_config["pickups_state"] = ammo_pickup_config.pop("items_state")
    for state in ammo_pickup_config["pickups_state"].values():
        state["requires_main_item"] = state.pop("requires_major_item")
    preset["configuration"]["ammo_pickup_configuration"] = ammo_pickup_config

    std_pickup_config = preset["configuration"].pop("major_items_configuration")
    std_pickup_config["pickups_state"] = std_pickup_config.pop("items_state")
    for state in std_pickup_config["pickups_state"].values():
        if "num_included_in_starting_items" in state:
            state["num_included_in_starting_pickups"] = state.pop("num_included_in_starting_items")
    std_pickup_config["default_pickups"] = std_pickup_config.pop("default_items")
    std_pickup_config["minimum_random_starting_pickups"] = std_pickup_config.pop("minimum_random_starting_items")
    std_pickup_config["maximum_random_starting_pickups"] = std_pickup_config.pop("maximum_random_starting_items")
    preset["configuration"]["standard_pickup_configuration"] = std_pickup_config

    return preset


def _migrate_v49(preset: dict) -> dict:
    if preset["game"] == "dread":
        config = preset["configuration"]
        flash_shift_config: dict = config["standard_pickup_configuration"]["pickups_state"]["Flash Shift"]
        ammo_config: dict = config["ammo_pickup_configuration"]["pickups_state"]

        # check to make sure preset wasn't manually migrated
        if flash_shift_config.get("included_ammo") is None:
            # 2 is the vanilla chain limit; include this many upgrades by default
            flash_shift_config["included_ammo"] = [2]
            config["standard_pickup_configuration"]["pickups_state"]["Flash Shift"] = flash_shift_config

        if ammo_config.get("Flash Shift Upgrade") is None:
            ammo_config["Flash Shift Upgrade"] = {
                "ammo_count": [1],
                "pickup_count": 0,
                "requires_main_item": True,
            }
            preset["configuration"]["ammo_pickup_configuration"]["pickups_state"] = ammo_config

    return preset


def _migrate_v50(preset: dict) -> dict:
    if preset["game"] == "dread":
        preset["configuration"]["raven_beak_damage_table_handling"] = "consistent_low"
    return preset


def _migrate_v51(preset: dict) -> dict:
    # and starting this version, `weaknesses` is also a valid value
    dock_rando = preset["configuration"]["dock_rando"]
    if dock_rando["mode"] in ("one-way", "two-way"):
        dock_rando["mode"] = "docks"

    return preset


def _migrate_v52(preset: dict) -> dict:
    def _fix(target):
        target["region"] = target.pop("world_name")
        target["area"] = target.pop("area_name")
        target["node"] = target.pop("node_name")

    config = preset["configuration"]

    for location in config["starting_location"]:
        _fix(location)

    if "elevators" in config:
        for location in config["elevators"]["excluded_teleporters"]:
            _fix(location)
        for location in config["elevators"]["excluded_targets"]:
            _fix(location)

    return preset


def _migrate_v53(preset: dict) -> dict:
    return _update_default_dock_rando_for_game(preset, RandovaniaGame.METROID_PRIME_ECHOES)


def _migrate_v54(preset: dict) -> dict:
    if preset["game"] == "prime2":
        preset["configuration"]["blue_save_doors"] = False
    return preset


def _migrate_v55(preset: dict) -> dict:
    game = preset["game"]
    if game in {"blank", "cave_story", "am2r"}:
        return preset
    preset["configuration"]["dock_rando"]["types_state"]["teleporter"] = {"can_change_from": [], "can_change_to": []}
    return preset


def _migrate_v56(preset: dict) -> dict:
    if preset["game"] in {"dread", "samus_returns", "prime3"}:
        preset["configuration"].pop("elevators")

    return preset


def _migrate_v57(preset: dict) -> dict:
    types_table = {
        "am2r": ["tunnel", "teleporter", "other"],
        "blank": ["other"],
        "cave_story": ["door", "trigger", "entrance", "exit", "teleporter", "debug cat", "other"],
        "dread": ["tunnel", "other", "teleporter"],
        "prime1": ["morph_ball", "other", "teleporter"],
        "prime2": ["morph_ball", "other", "teleporter"],
        "prime3": ["door", "morph_ball", "other", "teleporter"],
        "samus_returns": ["door", "tunnel", "other", "teleporter"],
        "super_metroid": ["door", "morph_ball", "other", "teleporter"],
    }

    for type_name in types_table[preset["game"]]:
        preset["configuration"]["dock_rando"]["types_state"].pop(type_name)

    return preset


def _migrate_v58(preset: dict) -> dict:
    config = preset["configuration"]
    game = preset["game"]

    if game in {"prime1", "prime2", "prime3"}:
        mapping = migration_data.get_raw_data(RandovaniaGame(game))["rename_teleporter_nodes"]

        def replace_location(old_location):
            identifier = f'{old_location["region"]}/{old_location["area"]}/{old_location["node"]}'
            new_node_name = mapping.get(identifier, None)
            if new_node_name is not None:
                old_location["node"] = new_node_name

        for old_location in config["starting_location"]:
            replace_location(old_location)

        if game in {"prime1", "prime2"}:
            elevators = config["elevators"]
            excluded_teleporters = elevators["excluded_teleporters"]
            for teleporter_obj in excluded_teleporters:
                replace_location(teleporter_obj)

            excluded_targets = elevators["excluded_targets"]
            for target_obj in excluded_targets:
                replace_location(target_obj)

    return preset


def _migrate_v59(preset: dict) -> dict:
    game = preset["game"]

    if game != "prime1":
        return preset

    configuration = preset["configuration"]

    dock_rando = configuration.get("dock_rando")
    if dock_rando is None:
        return preset

    types_state = dock_rando.get("types_state")
    if types_state is None:
        return preset

    door = types_state.get("door")
    if door is None:
        return preset

    can_change_to: list[str] = door.get("can_change_to")
    if can_change_to is None:
        return preset

    for i, x in enumerate(can_change_to):
        if x == "Charge Beam Door":
            can_change_to[i] = "Charge Beam Blast Shield"
        elif x == "Bomb Door":
            can_change_to[i] = "Bomb Blast Shield"

    return preset


def _migrate_v60(preset: dict) -> dict:
    preset["configuration"]["check_if_beatable_after_base_patches"] = False

    return preset


def _migrate_v61(preset: dict) -> dict:
    config = preset["configuration"]
    game = preset["game"]

    if game in {"dread"}:
        config["elevators"] = {
            "mode": "vanilla",
            "excluded_teleporters": [],
            "excluded_targets": [],
        }

    return preset


def _migrate_v62(preset: dict) -> dict:
    config = preset["configuration"]
    if "elevators" in config:
        if config["elevators"]["mode"] == "one-way-elevator":
            config["elevators"]["mode"] = "one-way-teleporter"
        elif config["elevators"]["mode"] == "one-way-elevator-replacement":
            config["elevators"]["mode"] = "one-way-teleporter-replacement"
        config["teleporters"] = config.pop("elevators")
    return preset


def _migrate_v63(preset: dict) -> dict:
    if preset["game"] == "prime1":
        if preset["configuration"]["qol_cutscenes"] in ["original", "skippable"]:
            preset["configuration"]["qol_cutscenes"] = "skippable"
        else:
            preset["configuration"]["qol_cutscenes"] = "skippablecompetitive"

    return preset


def _migrate_v64(preset: dict) -> dict:
    if preset["game"] == "prime1":
        x: str = preset["configuration"]["qol_cutscenes"]
        if x == "skippablecompetitive":
            x = "SkippableCompetitive"
        else:
            x = x.title()

        preset["configuration"]["qol_cutscenes"] = x
    return preset


def _migrate_v65(preset: dict) -> dict:
    config = preset["configuration"]
    game = preset["game"]

    if game == "dread":
        config["nerf_power_bombs"] = False
    return preset


def _migrate_v66(preset: dict) -> dict:
    if preset["game"] == "cave_story":
        # Exclude the items in hell from having progression.
        # This could be very bad in multiworld
        excluded = set(preset["configuration"]["available_locations"]["excluded_indices"])
        excluded = excluded.union(
            (
                30,
                31,
            )
        )
        preset["configuration"]["available_locations"]["excluded_indices"] = sorted(excluded)

    return preset


def _migrate_v67(preset: dict) -> dict:
    if preset["game"] == "prime1":
        preset["configuration"]["ingame_difficulty"] = "Normal"

    return preset


def _migrate_v68(preset: dict) -> dict:
    preset["configuration"]["single_set_for_pickups_that_solve"] = True
    preset["configuration"]["staggered_multi_pickup_placement"] = True
    return preset


def _migrate_v69(preset: dict) -> dict:
    if preset["game"] == "am2r":
        preset["configuration"]["artifacts"]["prefer_anywhere"] = False

    return preset


def _migrate_v70(preset: dict) -> dict:
    if preset["game"] == "am2r":
        preset["configuration"]["blue_save_doors"] = False

    return preset


def _migrate_v71(preset: dict) -> dict:
    if preset["game"] == "am2r":
        preset["configuration"]["force_blue_labs"] = False

    return preset


def _migrate_v72(preset: dict) -> dict:
    if preset["game"] == "prime1":
        preset["configuration"]["artifact_required"] = preset["configuration"]["artifact_target"]

    return preset


def _migrate_v73(preset: dict) -> dict:
    if preset["game"] == "dread":
        preset["configuration"]["warp_to_start"] = True

    return preset


def _migrate_v74(preset: dict) -> dict:
    if preset["game"] == "dread":
        difficulty_levels = ["beginner", "intermediate", "advanced", "expert", "hypermode"]

        floor_clips = [
            difficulty_levels.index(v)
            for k, v in preset["configuration"]["trick_level"]["specific_levels"].items()
            if k in ["ADC", "SSC"]
        ]

        if floor_clips:
            preset["configuration"]["trick_level"]["specific_levels"]["FloorClip"] = difficulty_levels[min(floor_clips)]

    return preset


def _migrate_v75(preset: dict) -> dict:
    if preset["game"] == "am2r":
        new_ammo_mapping = {
            "Missile Expansion": "Missile Tank",
            "Super Missile Expansion": "Super Missile Tank",
            "Power Bomb Expansion": "Power Bomb Tank",
        }
        pickups = preset["configuration"]["ammo_pickup_configuration"]["pickups_state"]
        for key in list(pickups):
            if key in new_ammo_mapping:
                pickups[new_ammo_mapping[key]] = pickups.pop(key)

    return preset


def _migrate_v76(preset: dict) -> dict:
    if preset["game"] == "samus_returns":
        preset = _update_default_dock_rando(preset)
    return preset


def _migrate_v77(preset: dict) -> dict:
    if preset["game"] == "am2r":
        preset["configuration"]["teleporters"] = {"mode": "vanilla", "excluded_teleporters": [], "excluded_targets": []}

    return preset


def _migrate_v78(preset: dict) -> dict:
    if preset["game"] == "samus_returns":
        preset["configuration"]["teleporters"] = {"mode": "vanilla", "excluded_teleporters": [], "excluded_targets": []}

    return preset


def _migrate_v79(preset: dict) -> dict:
    if preset["game"] == "am2r":
        preset["configuration"]["artifacts"]["placed_artifacts"] = preset["configuration"]["artifacts"][
            "required_artifacts"
        ]

    return preset


def _migrate_v80(preset: dict) -> dict:
    if preset["game"] == "am2r":
        items = ["Long Beam", "Infinite Bomb Propulsion", "Walljump Boots"]
        for i in items:
            preset["configuration"]["standard_pickup_configuration"]["pickups_state"][i] = {
                "num_included_in_starting_pickups": 1
            }

    return preset


def _migrate_v81(preset: dict) -> dict:
    if preset["game"] == "prime1":
        progressive_damage_reduction = preset["configuration"].pop("progressive_damage_reduction", False)
        if progressive_damage_reduction:
            damage_reduction = "Progressive"
        else:
            damage_reduction = "Default"
        preset["configuration"]["damage_reduction"] = damage_reduction

    return preset


def _migrate_v82(preset: dict) -> dict:
    if preset["game"] == "am2r":
        config = preset["configuration"]
        config["darkness_chance"] = 0
        config["darkness_min"] = 0
        config["darkness_max"] = 4
        config["submerged_water_chance"] = 0
        config["submerged_lava_chance"] = 0

    return preset


def _migrate_v83(preset: dict) -> dict:
    if preset["game"] == "samus_returns":
        config = preset["configuration"]
        config["constant_heat_damage"] = config["constant_lava_damage"] = 20

    return preset


def _migrate_v84(preset: dict) -> dict:
    if preset["game"] == "samus_returns":
        preset["configuration"]["hints"]["baby_metroid"] = "hide-area"

    return preset


_MIGRATIONS = [
    _migrate_v1,  # v1.1.1-247-gaf9e4a69
    _migrate_v2,  # v1.2.2-71-g0fbabe91
    _migrate_v3,  # v1.2.2-563-g50f4d07a
    _migrate_v4,  # v1.2.2-832-gec9b8004
    _migrate_v5,  # v2.0.2-15-g1096103d
    _migrate_v6,  # v2.1.2-61-g8bb33489
    _migrate_v7,  # v2.3.0-27-g6b4168b8
    _migrate_v8,  # v2.5.2-39-g3cf0b27d
    _migrate_v9,  # v2.6.1-33-gf0b8ec32
    _migrate_v10,  # v2.6.1-416-g358711ce
    _migrate_v11,  # v2.6.1-494-g086eb8cf
    _migrate_v12,  # v3.0.2-13-gdffb4b9a
    _migrate_v13,  # v3.1.3-122-g9f50c418
    _migrate_v14,  # v3.2.1-44-g11823eac
    _migrate_v15,  # v3.2.1-203-g6e303090
    _migrate_v16,  # v3.2.1-363-g3a93b533
    _migrate_v17,
    _migrate_v18,
    _migrate_v19,  # v3.3.0dev721
    _migrate_v20,
    _migrate_v21,
    _migrate_v22,
    _migrate_v23,
    _migrate_v24,
    _migrate_v25,
    _migrate_v26,
    _migrate_v27,
    _migrate_v28,
    _migrate_v29,
    _migrate_v30,
    _migrate_v31,
    _migrate_v32,
    _migrate_v33,
    _migrate_v34,
    _migrate_v35,
    _migrate_v36,
    _migrate_v37,
    _migrate_v38,
    _migrate_v39,
    _migrate_v40,
    _migrate_v41,
    _migrate_v42,
    _migrate_v43,
    _migrate_v44,
    _migrate_v45,
    _migrate_v46,
    _migrate_v47,
    _migrate_v48,
    _migrate_v49,
    _migrate_v50,
    _migrate_v51,
    _migrate_v52,
    _migrate_v53,
    _migrate_v54,
    _migrate_v55,
    _migrate_v56,
    _migrate_v57,
    _migrate_v58,
    _migrate_v59,
    _migrate_v60,
    _migrate_v61,
    _migrate_v62,
    _migrate_v63,
    _migrate_v64,
    _migrate_v65,
    _migrate_v66,
    _migrate_v67,
    _migrate_v68,
    _migrate_v69,
    _migrate_v70,
    _migrate_v71,
    _migrate_v72,
    _migrate_v73,
    _migrate_v74,
    _migrate_v75,
    _migrate_v76,  # msr door lock rando
    _migrate_v77,
    _migrate_v78,  # msr elevator rando
    _migrate_v79,
    _migrate_v80,
    _migrate_v81,
    _migrate_v82,
    _migrate_v83,
    _migrate_v84,
]
CURRENT_VERSION = migration_lib.get_version(_MIGRATIONS)


def convert_to_current_version(preset: dict) -> dict:
    return migration_lib.apply_migrations(
        preset,
        _MIGRATIONS,
        version_name="preset version",
    )
