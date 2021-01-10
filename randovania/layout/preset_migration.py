import copy
import json
from pathlib import Path
from typing import Optional, Dict

import aiofiles
import slugify

from randovania.games.game import RandovaniaGame
from randovania.layout.preset import Preset

CURRENT_PRESET_VERSION = 8


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
    layout_configuration["energy_per_tank"] = 100.0
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
        "allowed_as_random_starting_item": True
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


_MIGRATIONS = {
    1: _migrate_v1,
    2: _migrate_v2,
    3: _migrate_v3,
    4: _migrate_v4,
    5: _migrate_v5,
    6: _migrate_v6,
    7: _migrate_v7,
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
        if self.data is None:
            return self._preset.name
        else:
            return self.data["name"]

    @property
    def game(self) -> RandovaniaGame:
        if self.data is None:
            return self._preset.configuration.game

        if self.data["schema_version"] < 6:
            return RandovaniaGame.PRIME2

        return RandovaniaGame(self.data["game"])

    def __eq__(self, other):
        if isinstance(other, VersionedPreset):
            return self.get_preset() == other.get_preset()
        return False

    @property
    def _converted(self):
        return self._preset is not None or self.exception is not None

    def ensure_converted(self):
        if not self._converted:
            try:
                self._preset = Preset.from_json_dict(convert_to_current_version(copy.deepcopy(self.data)))
            except (ValueError, KeyError) as e:
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
