import copy
import io
import json
import math
import uuid
from pathlib import Path
from typing import Optional, Dict

import aiofiles
import slugify

from randovania.game_description.world.area_location import AreaLocation
from randovania.games.game import RandovaniaGame
from randovania.layout.preset import Preset

CURRENT_PRESET_VERSION = 14


class InvalidPreset(Exception):
    def __init__(self, original_exception: Exception):
        self.original_exception = original_exception


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
    from randovania.game_description import default_database
    game = default_database.game_description_for(RandovaniaGame(preset["game"]))

    def _name_to_location(name: str):
        world_name, area_name = name.split("/", 1)
        world = game.world_list.world_with_name(world_name)
        area = world.area_by_name(area_name)
        return AreaLocation(world.world_asset_id, area.area_asset_id)

    preset["configuration"]["multi_pickup_placement"] = False

    if "energy_per_tank" in preset["configuration"]:
        preset["configuration"]["energy_per_tank"] = int(preset["configuration"]["energy_per_tank"])

    preset["configuration"]["starting_location"] = [
        _name_to_location(location).as_json
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


_MIGRATIONS = {
    1: _migrate_v1,
    2: _migrate_v2,
    3: _migrate_v3,
    4: _migrate_v4,
    5: _migrate_v5,
    6: _migrate_v6,
    7: _migrate_v7,
    8: _migrate_v8,
    9: _migrate_v9,
    10: _migrate_v10,
    11: _migrate_v11,
    12: _migrate_v12,
    13: _migrate_v13,
}


def _apply_migration(preset: dict, version: int) -> dict:
    while version < CURRENT_PRESET_VERSION:
        preset = _MIGRATIONS[version](preset)
        version += 1
    return preset


def convert_to_current_version(preset: dict) -> dict:
    schema_version = preset["schema_version"]
    if schema_version > CURRENT_PRESET_VERSION:
        raise ValueError(f"Unknown version: {schema_version}")

    if schema_version < CURRENT_PRESET_VERSION:
        return _apply_migration(preset, schema_version)
    else:
        return preset


class VersionedPreset:
    data: dict
    exception: Optional[InvalidPreset] = None
    _preset: Optional[Preset] = None

    def __init__(self, data):
        self.data = data

    @classmethod
    def file_extension(cls) -> str:
        return "rdvpreset"

    @property
    def slug_name(self) -> str:
        return slugify.slugify(self.name)

    @property
    def name(self) -> str:
        if self._preset is not None:
            return self._preset.name
        else:
            return self.data["name"]

    @property
    def base_preset_uuid(self) -> Optional[uuid.UUID]:
        if self._preset is not None:
            return self._preset.base_preset_uuid
        elif self.data["base_preset_uuid"] is not None:
            return uuid.UUID(self.data["base_preset_uuid"])

    @property
    def game(self) -> RandovaniaGame:
        if self._preset is not None:
            return self._preset.configuration.game

        if self.data["schema_version"] < 6:
            return RandovaniaGame.METROID_PRIME_ECHOES

        return RandovaniaGame(self.data["game"])

    @property
    def uuid(self) -> uuid.UUID:
        if self._preset is not None:
            return self._preset.uuid
        else:
            return uuid.UUID(self.data["uuid"])

    def __eq__(self, other):
        if isinstance(other, VersionedPreset):
            return self.get_preset() == other.get_preset()
        return False

    def is_for_known_game(self):
        try:
            # self.game is never None, but it might raise ValueError in case the preset is for an unknown game
            return self.game is not None
        except ValueError:
            return False

    @property
    def _converted(self):
        return self._preset is not None or self.exception is not None

    def ensure_converted(self):
        if not self._converted:
            try:
                self._preset = Preset.from_json_dict(convert_to_current_version(copy.deepcopy(self.data)))
            except (ValueError, KeyError, TypeError) as e:
                self.exception = InvalidPreset(e)
                raise self.exception from e

    def get_preset(self) -> Preset:
        self.ensure_converted()
        if self.exception:
            raise self.exception
        else:
            return self._preset

    @classmethod
    async def from_file(cls, path: Path) -> "VersionedPreset":
        async with aiofiles.open(path) as f:
            return VersionedPreset(json.loads(await f.read()))

    @classmethod
    def from_file_sync(cls, path: Path) -> "VersionedPreset":
        with path.open() as f:
            return VersionedPreset(json.load(f))

    @classmethod
    def with_preset(cls, preset: Preset) -> "VersionedPreset":
        result = VersionedPreset(None)
        result._preset = preset
        return result

    def save_to_file(self, path: Path):
        path.parent.mkdir(exist_ok=True, parents=True)
        with path.open("w") as preset_file:
            json.dump(self.as_json, preset_file, indent=4)

    def save_to_io(self, data: io.BytesIO):
        data.write(
            json.dumps(self.as_json, indent=4).encode("utf-8")
        )

    @property
    def as_json(self) -> dict:
        if self._preset is not None:
            preset_json = {
                "schema_version": CURRENT_PRESET_VERSION,
            }
            preset_json.update(self._preset.as_json)
            return preset_json
        else:
            assert self.data is not None
            return self.data
