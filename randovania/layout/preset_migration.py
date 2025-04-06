from __future__ import annotations

import copy
import math
import uuid

from randovania.game.game_enum import RandovaniaGame
from randovania.game_description import migration_data
from randovania.lib import migration_lib


def _migrate_v1(preset: dict, game: RandovaniaGame) -> None:
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


def _migrate_v2(preset: dict, game: RandovaniaGame) -> None:
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


def _migrate_v3(preset: dict, game: RandovaniaGame) -> None:
    preset["layout_configuration"]["safe_zone"] = {
        "fully_heal": True,
        "prevents_dark_aether": True,
        "heal_per_second": 1.0,
    }


def _migrate_v4(preset: dict, game: RandovaniaGame) -> None:
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


def _migrate_v5(preset: dict, game: RandovaniaGame) -> None:
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
    for item, state in default_items_state.items():
        if item not in major_items:
            major_items[item] = state

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


def _migrate_v6(preset: dict, game: RandovaniaGame) -> None:
    preset["configuration"]["dangerous_energy_tank"] = False


def _migrate_v7(preset: dict, game: RandovaniaGame) -> None:
    default_items = {}
    if game == RandovaniaGame.METROID_PRIME_ECHOES:
        default_items["visor"] = "Combat Visor"
        default_items["beam"] = "Power Beam"

    preset["configuration"]["major_items_configuration"]["default_items"] = default_items


def _migrate_v8(preset: dict, game: RandovaniaGame) -> None:
    migration = migration_data.get_raw_data(game)

    def _name_to_location(name: str) -> dict[str, int]:
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
    if game == RandovaniaGame.METROID_PRIME_ECHOES:
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


def _migrate_v9(preset: dict, game: RandovaniaGame) -> None:
    if preset.get("uuid") is None:
        preset["uuid"] = str(uuid.uuid4())

    _name_to_uuid = {
        "Darkszero's Deluxe": "ea1eced4-53b8-4bb3-a08f-27ac1afe6aab",
        "Fewest Changes": "bba48268-0710-4ac5-baae-dcd5fcd31d80",
        "Prime Preset": "e36f52b3-ccd9-4dd7-a18f-b57b25f6b079",
        "Starter Preset": "fcbe4e3f-b1fa-41cc-83cb-c86d84c10f0f",
    }

    base_preset_name = preset.pop("base_preset_name")
    preset["base_preset_uuid"] = _name_to_uuid.get(base_preset_name, str(uuid.uuid4()))

    if game != RandovaniaGame.METROID_PRIME_ECHOES:
        preset["configuration"].pop("dangerous_energy_tank")


def _migrate_v10(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.METROID_PRIME:
        major = preset["configuration"].pop("qol_major_cutscenes")
        minor = preset["configuration"].pop("qol_minor_cutscenes")
        if major:
            cutscenes = "major"
        elif minor:
            cutscenes = "minor"
        else:
            cutscenes = "original"
        preset["configuration"]["qol_cutscenes"] = cutscenes

    elif game == RandovaniaGame.METROID_PRIME_ECHOES:
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


def _migrate_v11(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.METROID_PRIME:
        preset["configuration"]["warp_to_start"] = False


def _migrate_v12(preset: dict, game: RandovaniaGame) -> None:
    preset["configuration"]["logical_resource_action"] = "randomly"
    if game == RandovaniaGame.METROID_PRIME:
        preset["configuration"]["artifact_target"] = preset["configuration"].pop("artifacts")
        preset["configuration"]["artifact_minimum_progression"] = 0
        preset["configuration"]["qol_pickup_scans"] = False


def _migrate_v13(preset: dict, game: RandovaniaGame) -> None:
    for config in preset["configuration"]["major_items_configuration"]["items_state"].values():
        config.pop("allowed_as_random_starting_item", None)

    maximum_ammo = preset["configuration"]["ammo_configuration"].pop("maximum_ammo")
    ammo_ids = {
        RandovaniaGame.METROID_PRIME: {
            "Missile Expansion": ["4"],
            "Power Bomb Expansion": ["7"],
        },
        RandovaniaGame.METROID_PRIME_ECHOES: {
            "Missile Expansion": ["44"],
            "Power Bomb Expansion": ["43"],
            "Dark Ammo Expansion": ["45"],
            "Light Ammo Expansion": ["46"],
            "Beam Ammo Expansion": ["45", "46"],
        },
    }[game]
    main_items = {
        RandovaniaGame.METROID_PRIME: {
            "Missile Launcher": ["4"],
            "Power Bomb": ["7"],
        },
        RandovaniaGame.METROID_PRIME_ECHOES: {
            "Dark Beam": ["45"],
            "Light Beam": ["46"],
            "Annihilator Beam": ["45", "46"],
            "Missile Launcher": ["44"],
            "Seeker Launcher": ["44"],
            "Power Bomb": ["43"],
        },
    }

    for item, ids in main_items[game].items():
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


def _migrate_v14(preset: dict, game: RandovaniaGame) -> None:
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


def _migrate_v15(preset: dict, game: RandovaniaGame) -> None:
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

    if game == RandovaniaGame.METROID_PRIME_ECHOES:
        translator_configuration = preset["configuration"]["translator_configuration"]
        old = translator_configuration["translator_requirement"]
        translator_configuration["translator_requirement"] = {
            identifier: old[str(gate_index)] for identifier, gate_index in gate_mapping.items()
        }


def _migrate_v16(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.METROID_PRIME:
        art_hints = {"artifacts": "precise"}
        preset["configuration"]["hints"] = art_hints


def _migrate_v17(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.METROID_PRIME:
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


def _migrate_v18(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.METROID_PRIME:
        preset["configuration"]["shuffle_item_pos"] = False
        preset["configuration"]["items_every_room"] = False


def _migrate_v19(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.CAVE_STORY:
        itemconfig = preset["configuration"]["major_items_configuration"]["items_state"]
        ammoconfig = preset["configuration"]["ammo_configuration"]["items_state"]

        if itemconfig.get("Base Missiles") is not None:
            # handles presets which were hand-migrated before this func was written
            return

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


def _migrate_v20(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.METROID_PRIME:
        preset["configuration"]["spring_ball"] = False


def _migrate_v21(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.METROID_PRIME:
        preset["configuration"]["deterministic_idrone"] = True


def _migrate_v22(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.METROID_DREAD:
        preset["configuration"].pop("disable_adam_convos")


def _migrate_v23(preset: dict, game: RandovaniaGame) -> None:
    preset["configuration"]["first_progression_must_be_local"] = False


def _migrate_v24(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.METROID_PRIME:
        preset["configuration"]["deterministic_maze"] = True


def _migrate_v25(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.METROID_PRIME:
        preset["configuration"]["random_boss_sizes"] = False
        preset["configuration"]["no_doors"] = False
        preset["configuration"]["superheated_probability"] = 0
        preset["configuration"]["submerged_probability"] = 0
        preset["configuration"]["room_rando"] = "None"
        preset["configuration"]["large_samus"] = False


def _migrate_v26(preset: dict, game: RandovaniaGame) -> None:
    preset["configuration"]["minimum_available_locations_for_hint_placement"] = 0
    preset["configuration"]["minimum_location_weight_for_hint_placement"] = 0.0
    if game == RandovaniaGame.METROID_DREAD:
        preset["configuration"]["immediate_energy_parts"] = True


def _migrate_v27(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.METROID_PRIME and "phazon_suit" not in preset["configuration"]["hints"].keys():
        preset["configuration"]["hints"]["phazon_suit"] = "hide-area"


def _migrate_v28(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.METROID_DREAD:
        for config in ["hanubia_shortcut_no_grapple", "hanubia_easier_path_to_itorash", "extra_pickups_for_bosses"]:
            preset["configuration"][config] = True


def _migrate_v29(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.METROID_DREAD:
        preset["configuration"]["x_starts_released"] = False


def _migrate_v30(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.METROID_DREAD:
        for item in ("Metroid Suit", "Hyper Beam", "Power Suit", "Power Beam"):
            preset["configuration"]["major_items_configuration"]["items_state"].pop(item)


def _migrate_v31(preset: dict, game: RandovaniaGame) -> None:
    preset["configuration"]["multi_pickup_new_weighting"] = False


def _update_default_dock_rando(preset: dict, game: RandovaniaGame) -> None:
    preset["configuration"]["dock_rando"] = {
        "mode": "vanilla",
        "types_state": copy.deepcopy(migration_data.get_default_dock_lock_settings(game)),
    }


def _migrate_v32(preset: dict, game: RandovaniaGame) -> None:
    _update_default_dock_rando(preset, game)


def _migrate_v33(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.METROID_DREAD:
        preset["configuration"].pop("extra_pickups_for_bosses")
        preset["configuration"]["artifacts"] = {
            "prefer_emmi": True,
            "prefer_major_bosses": True,
            "required_artifacts": 0,
        }


def _migrate_v34(preset: dict, game: RandovaniaGame) -> None:
    preset["configuration"].pop("multi_pickup_placement")
    preset["configuration"].pop("multi_pickup_new_weighting")


def _migrate_v35(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.METROID_DREAD:
        preset["configuration"]["linear_damage_runs"] = False
        preset["configuration"]["linear_dps"] = 20


def _migrate_v36(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.METROID_PRIME:
        preset["configuration"]["enemy_attributes"] = None


def _migrate_v37(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.METROID_DREAD:
        config = preset["configuration"]
        damage = config.pop("linear_dps")
        if not config.pop("linear_damage_runs"):
            damage = None
        config["constant_heat_damage"] = config["constant_cold_damage"] = config["constant_lava_damage"] = damage


def _migrate_v38(preset: dict, game: RandovaniaGame) -> None:
    # New version since we don't write the base_preset_uuid to the preset itself anymore
    # But leave it there to migrate easily to options
    return


def _migrate_v39(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.METROID_DREAD:
        preset["configuration"]["allow_highly_dangerous_logic"] = False


def _migrate_v40(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.METROID_PRIME:
        preset["configuration"]["blue_save_doors"] = False


def _migrate_v41(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.METROID_PRIME_ECHOES:
        preset["configuration"]["use_new_patcher"] = False
        preset["configuration"]["inverted_mode"] = False


def _migrate_v42(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.METROID_DREAD:
        _update_default_dock_rando(preset, game)


def _migrate_v43(preset: dict, game: RandovaniaGame) -> None:
    preset["configuration"]["single_set_for_pickups_that_solve"] = False
    preset["configuration"]["staggered_multi_pickup_placement"] = False


def _migrate_v44(preset: dict, game: RandovaniaGame) -> None:
    def add_node_name(location: dict) -> None:
        node_name = migration_data.get_node_name_for_area(game, location["world_name"], location["area_name"])
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


def _migrate_v45(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.METROID_PRIME_ECHOES:
        preset["configuration"]["portal_rando"] = False


def _migrate_v46(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.METROID_DREAD:
        preset["configuration"]["april_fools_hints"] = False


def _migrate_v47(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.METROID_PRIME:
        preset["configuration"].pop("deterministic_idrone")
        preset["configuration"].pop("deterministic_maze")
        preset["configuration"].pop("qol_game_breaking")
        preset["configuration"].pop("qol_pickup_scans")
        preset["configuration"].pop("heat_protection_only_varia")
        preset["configuration"]["legacy_mode"] = False


def _migrate_v48(preset: dict, game: RandovaniaGame) -> None:
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


def _migrate_v49(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.METROID_DREAD:
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


def _migrate_v50(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.METROID_DREAD:
        preset["configuration"]["raven_beak_damage_table_handling"] = "consistent_low"


def _migrate_v51(preset: dict, game: RandovaniaGame) -> None:
    # and starting this version, `weaknesses` is also a valid value
    dock_rando = preset["configuration"]["dock_rando"]
    if dock_rando["mode"] in ("one-way", "two-way"):
        dock_rando["mode"] = "docks"


def _migrate_v52(preset: dict, game: RandovaniaGame) -> None:
    def _fix(target: dict) -> None:
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


def _migrate_v53(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.METROID_PRIME_ECHOES:
        _update_default_dock_rando(preset, RandovaniaGame.METROID_PRIME_ECHOES)


def _migrate_v54(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.METROID_PRIME_ECHOES:
        preset["configuration"]["blue_save_doors"] = False


def _migrate_v55(preset: dict, game: RandovaniaGame) -> None:
    if game in {RandovaniaGame.BLANK, RandovaniaGame.CAVE_STORY, RandovaniaGame.AM2R}:
        return
    preset["configuration"]["dock_rando"]["types_state"]["teleporter"] = {"can_change_from": [], "can_change_to": []}


def _migrate_v56(preset: dict, game: RandovaniaGame) -> None:
    if game in {
        RandovaniaGame.METROID_DREAD,
        RandovaniaGame.METROID_SAMUS_RETURNS,
    }:
        preset["configuration"].pop("elevators")


def _migrate_v57(preset: dict, game: RandovaniaGame) -> None:
    types_table = {
        RandovaniaGame.AM2R: ["tunnel", "teleporter", "other"],
        RandovaniaGame.BLANK: ["other"],
        RandovaniaGame.CAVE_STORY: ["door", "trigger", "entrance", "exit", "teleporter", "debug cat", "other"],
        RandovaniaGame.METROID_DREAD: ["tunnel", "other", "teleporter"],
        RandovaniaGame.METROID_PRIME: ["morph_ball", "other", "teleporter"],
        RandovaniaGame.METROID_PRIME_ECHOES: ["morph_ball", "other", "teleporter"],
        RandovaniaGame.METROID_SAMUS_RETURNS: ["door", "tunnel", "other", "teleporter"],
    }

    for type_name in types_table[game]:
        preset["configuration"]["dock_rando"]["types_state"].pop(type_name)


def _migrate_v58(preset: dict, game: RandovaniaGame) -> None:
    config = preset["configuration"]

    if game in {
        RandovaniaGame.METROID_PRIME,
        RandovaniaGame.METROID_PRIME_ECHOES,
    }:
        mapping = migration_data.get_raw_data(game)["rename_teleporter_nodes"]

        def replace_location(old_location: dict) -> None:
            identifier = f"{old_location['region']}/{old_location['area']}/{old_location['node']}"
            new_node_name = mapping.get(identifier, None)
            if new_node_name is not None:
                old_location["node"] = new_node_name

        for old_location in config["starting_location"]:
            replace_location(old_location)

        if game in {RandovaniaGame.METROID_PRIME, RandovaniaGame.METROID_PRIME_ECHOES}:
            elevators = config["elevators"]
            excluded_teleporters = elevators["excluded_teleporters"]
            for teleporter_obj in excluded_teleporters:
                replace_location(teleporter_obj)

            excluded_targets = elevators["excluded_targets"]
            for target_obj in excluded_targets:
                replace_location(target_obj)


def _migrate_v59(preset: dict, game: RandovaniaGame) -> None:
    if game != RandovaniaGame.METROID_PRIME:
        return

    configuration = preset["configuration"]

    dock_rando = configuration.get("dock_rando")
    if dock_rando is None:
        return

    types_state = dock_rando.get("types_state")
    if types_state is None:
        return

    door = types_state.get("door")
    if door is None:
        return

    can_change_to: list[str] = door.get("can_change_to")
    if can_change_to is None:
        return

    for i, x in enumerate(can_change_to):
        if x == "Charge Beam Door":
            can_change_to[i] = "Charge Beam Blast Shield"
        elif x == "Bomb Door":
            can_change_to[i] = "Bomb Blast Shield"


def _migrate_v60(preset: dict, game: RandovaniaGame) -> None:
    preset["configuration"]["check_if_beatable_after_base_patches"] = False


def _migrate_v61(preset: dict, game: RandovaniaGame) -> None:
    config = preset["configuration"]

    if game == RandovaniaGame.METROID_DREAD:
        config["elevators"] = {
            "mode": "vanilla",
            "excluded_teleporters": [],
            "excluded_targets": [],
        }


def _migrate_v62(preset: dict, game: RandovaniaGame) -> None:
    config = preset["configuration"]
    if "elevators" in config:
        if config["elevators"]["mode"] == "one-way-elevator":
            config["elevators"]["mode"] = "one-way-teleporter"
        elif config["elevators"]["mode"] == "one-way-elevator-replacement":
            config["elevators"]["mode"] = "one-way-teleporter-replacement"
        config["teleporters"] = config.pop("elevators")


def _migrate_v63(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.METROID_PRIME:
        if preset["configuration"]["qol_cutscenes"] in ["original", "skippable"]:
            preset["configuration"]["qol_cutscenes"] = "skippable"
        else:
            preset["configuration"]["qol_cutscenes"] = "skippablecompetitive"


def _migrate_v64(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.METROID_PRIME:
        x: str = preset["configuration"]["qol_cutscenes"]
        if x == "skippablecompetitive":
            x = "SkippableCompetitive"
        else:
            x = x.title()

        preset["configuration"]["qol_cutscenes"] = x


def _migrate_v65(preset: dict, game: RandovaniaGame) -> None:
    config = preset["configuration"]

    if game == RandovaniaGame.METROID_DREAD:
        config["nerf_power_bombs"] = False


def _migrate_v66(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.CAVE_STORY:
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


def _migrate_v67(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.METROID_PRIME:
        preset["configuration"]["ingame_difficulty"] = "Normal"


def _migrate_v68(preset: dict, game: RandovaniaGame) -> None:
    preset["configuration"]["single_set_for_pickups_that_solve"] = True
    preset["configuration"]["staggered_multi_pickup_placement"] = True


def _migrate_v69(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.AM2R:
        preset["configuration"]["artifacts"]["prefer_anywhere"] = False


def _migrate_v70(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.AM2R:
        preset["configuration"]["blue_save_doors"] = False


def _migrate_v71(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.AM2R:
        preset["configuration"]["force_blue_labs"] = False


def _migrate_v72(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.METROID_PRIME:
        preset["configuration"]["artifact_required"] = preset["configuration"]["artifact_target"]


def _migrate_v73(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.METROID_DREAD:
        preset["configuration"]["warp_to_start"] = True


def _migrate_v74(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.METROID_DREAD:
        difficulty_levels = ["beginner", "intermediate", "advanced", "expert", "hypermode"]

        floor_clips = [
            difficulty_levels.index(v)
            for k, v in preset["configuration"]["trick_level"]["specific_levels"].items()
            if k in ["ADC", "SSC"]
        ]

        if floor_clips:
            preset["configuration"]["trick_level"]["specific_levels"]["FloorClip"] = difficulty_levels[min(floor_clips)]


def _migrate_v75(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.AM2R:
        new_ammo_mapping = {
            "Missile Expansion": "Missile Tank",
            "Super Missile Expansion": "Super Missile Tank",
            "Power Bomb Expansion": "Power Bomb Tank",
        }
        pickups = preset["configuration"]["ammo_pickup_configuration"]["pickups_state"]
        for key in list(pickups):
            if key in new_ammo_mapping:
                pickups[new_ammo_mapping[key]] = pickups.pop(key)


def _migrate_v76(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.METROID_SAMUS_RETURNS:
        _update_default_dock_rando(preset, game)


def _migrate_v77(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.AM2R:
        preset["configuration"]["teleporters"] = {"mode": "vanilla", "excluded_teleporters": [], "excluded_targets": []}


def _migrate_v78(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.METROID_SAMUS_RETURNS:
        preset["configuration"]["teleporters"] = {"mode": "vanilla", "excluded_teleporters": [], "excluded_targets": []}


def _migrate_v79(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.AM2R:
        preset["configuration"]["artifacts"]["placed_artifacts"] = preset["configuration"]["artifacts"][
            "required_artifacts"
        ]


def _migrate_v80(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.AM2R:
        items = ["Long Beam", "Infinite Bomb Propulsion", "Walljump Boots"]
        for i in items:
            preset["configuration"]["standard_pickup_configuration"]["pickups_state"][i] = {
                "num_included_in_starting_pickups": 1
            }


def _migrate_v81(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.METROID_PRIME:
        progressive_damage_reduction = preset["configuration"].pop("progressive_damage_reduction", False)
        if progressive_damage_reduction:
            damage_reduction = "Progressive"
        else:
            damage_reduction = "Default"
        preset["configuration"]["damage_reduction"] = damage_reduction


def _migrate_v82(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.AM2R:
        config = preset["configuration"]
        config["darkness_chance"] = 0
        config["darkness_min"] = 0
        config["darkness_max"] = 4
        config["submerged_water_chance"] = 0
        config["submerged_lava_chance"] = 0


def _migrate_v83(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.METROID_SAMUS_RETURNS:
        config = preset["configuration"]
        config["constant_heat_damage"] = config["constant_lava_damage"] = 20


def _migrate_v84(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.METROID_SAMUS_RETURNS:
        preset["configuration"]["hints"]["baby_metroid"] = "hide-area"


def _migrate_v85(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.AM2R:
        config = preset["configuration"]
        config["first_suit_dr"] = 50
        config["second_suit_dr"] = 75


def _migrate_v86(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.METROID_PRIME:
        state = preset["configuration"]["ammo_pickup_configuration"]["pickups_state"]
        item_list = [("Energy Refill", 20), ("Missile Refill", 5), ("Power Bomb Refill", 1)]
        for item_name, count in item_list:
            state[item_name] = {"ammo_count": [count], "pickup_count": 0, "requires_main_item": False}


def _migrate_v87(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.AM2R:
        config = preset["configuration"]
        config["vertically_flip_gameplay"] = False
        config["horizontally_flip_gameplay"] = False


def _migrate_v88(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.METROID_DREAD:
        config = preset["configuration"]
        config["freesink"] = False


def _migrate_v89(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.METROID_SAMUS_RETURNS:
        artifacts = preset["configuration"]["artifacts"]
        artifacts["placed_artifacts"] = artifacts["required_artifacts"]


def _migrate_v90(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.METROID_SAMUS_RETURNS:
        preset["configuration"]["final_boss"] = "Ridley"


def _migrate_v91(preset: dict, game: RandovaniaGame) -> None:
    preset["configuration"]["two_sided_door_lock_search"] = False


def _migrate_v92(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.METROID_PRIME:
        preset["configuration"]["remove_bars_great_tree_hall"] = False


def _migrate_v93(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.METROID_PRIME:
        preset["configuration"]["dock_rando"]["types_state"]["door"]["can_change_from"].remove("Missile Blast Shield")
        preset["configuration"]["dock_rando"]["types_state"]["door"]["can_change_from"].append(
            "Missile Blast Shield (randomprime)"
        )


def _migrate_v94(preset: dict, game: RandovaniaGame) -> None:
    preset["configuration"]["logical_pickup_placement"] = "minimal"


def _migrate_v95(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.METROID_SAMUS_RETURNS:
        hints = preset["configuration"]["hints"]
        hints["final_boss_item"] = hints["baby_metroid"]
        hints.pop("baby_metroid")


def _migrate_v96(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.METROID_DREAD:
        preset["configuration"]["disabled_lights"] = {
            "artaria": False,
            "burenia": False,
            "cataris": False,
            "dairon": False,
            "elun": False,
            "ferenia": False,
            "ghavoran": False,
            "hanubia": False,
            "itorash": False,
        }


def _migrate_v97(preset: dict, game: RandovaniaGame) -> None:
    preset["configuration"]["consider_possible_unsafe_resources"] = False


def _migrate_v98(preset: dict, game: RandovaniaGame) -> None:
    preset["configuration"]["use_resolver_hints"] = False


def _migrate_v99(preset: dict, game: RandovaniaGame) -> None:
    for trick, level in preset["configuration"]["trick_level"]["specific_levels"].items():
        if level == "hypermode":
            preset["configuration"]["trick_level"]["specific_levels"][trick] = "ludicrous"


def _migrate_v100(preset: dict, game: RandovaniaGame) -> None:
    config = preset["configuration"]
    hints_config = {}

    def pop_from_base_config(field: str) -> None:
        hints_config[field] = config.pop(field)

    pop_from_base_config("minimum_available_locations_for_hint_placement")
    pop_from_base_config("minimum_location_weight_for_hint_placement")
    pop_from_base_config("use_resolver_hints")

    if game in {
        RandovaniaGame.AM2R,
        RandovaniaGame.FUSION,
        RandovaniaGame.METROID_PRIME,
        RandovaniaGame.METROID_SAMUS_RETURNS,
    }:
        hints_config["specific_pickup_hints"] = config.pop("hints")
    elif game == RandovaniaGame.METROID_PRIME_ECHOES:
        hints_config["specific_pickup_hints"] = {"sky_temple_keys": config["hints"]["sky_temple_keys"]}
    else:
        hints_config["specific_pickup_hints"] = {}

    if game in {RandovaniaGame.CAVE_STORY, RandovaniaGame.METROID_PRIME_ECHOES}:
        hints_config["enable_random_hints"] = config.pop("hints")["item_hints"]
    else:
        hints_config["enable_random_hints"] = True

    hints_config["enable_specific_location_hints"] = True

    config["hints"] = hints_config


def _migrate_v101(preset: dict, game: RandovaniaGame) -> None:
    if game == RandovaniaGame.METROID_PRIME_ECHOES:
        banned_pickups = ["Cannon Ball", "Unlimited Beam Ammo", "Unlimited Missiles", "Double Damage"]
        pickup_config = preset["configuration"]["standard_pickup_configuration"]["pickups_state"]
        for pickup in banned_pickups:
            if pickup in pickup_config:
                if "num_included_in_starting_pickups" in pickup_config[pickup]:
                    pickup_config[pickup].pop("num_included_in_starting_pickups")


def _migrate_v102(preset: dict, game: RandovaniaGame) -> None:
    if game not in {RandovaniaGame.METROID_PRIME_ECHOES, RandovaniaGame.CAVE_STORY}:
        return

    rename = migration_data.get_raw_data(game)["in_dark_world_rename"]

    def fix(identifier: dict) -> None:
        region_rename = rename.get(f"{identifier['region']}/{identifier['area']}")
        if region_rename:
            identifier["region"] = region_rename
            if region_rename in {"Sky Temple", "Sky Temple Grounds"}:
                if identifier["node"] == "Elevator to Great Temple":
                    identifier["node"] = "Elevator to Sky Temple"
                elif identifier["node"] == "Elevator to Temple Grounds":
                    identifier["node"] = "Elevator to Sky Temple Grounds"

    for starting_location in preset["configuration"]["starting_location"]:
        fix(starting_location)

    if game == RandovaniaGame.METROID_PRIME_ECHOES:
        for it in preset["configuration"]["teleporters"]["excluded_teleporters"]:
            fix(it)
        for it in preset["configuration"]["teleporters"]["excluded_targets"]:
            fix(it)


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
    _migrate_v85,  # am2r configurable DR
    _migrate_v86,
    _migrate_v87,
    _migrate_v88,  # dread freesink
    _migrate_v89,  # msr configurable required dna
    _migrate_v90,  # msr configurable final boss
    _migrate_v91,  # two sided door search
    _migrate_v92,  # remove bars great tree hall
    _migrate_v93,  # update default dock_rando in Prime 1 to use RP Blast Shield Change
    _migrate_v94,
    _migrate_v95,  # msr rename baby_metroid hint to final_boss_item hint
    _migrate_v96,  # dread disable lights per region
    _migrate_v97,  # consider possible unsafe resources
    _migrate_v98,  # use resolver hints
    _migrate_v99,  # replace trick level hypermode with ludicrous
    _migrate_v100,  # hints configuration
    _migrate_v101,
    _migrate_v102,  # removal of in_dark_aether
]
CURRENT_VERSION = migration_lib.get_version(_MIGRATIONS)


def convert_to_current_version(preset: dict, game: RandovaniaGame) -> dict:
    return migration_lib.apply_migrations_with_game(
        preset,
        _MIGRATIONS,
        game,
        version_name="preset version",
    )
