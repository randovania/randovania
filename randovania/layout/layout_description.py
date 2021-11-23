import base64
import hashlib
import itertools
import json
import re
import typing
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from random import Random
from typing import Tuple, Dict

from randovania import get_data_path
from randovania.game_description import migration_data
from randovania.game_description.game_patches import GamePatches
from randovania.games.game import RandovaniaGame
from randovania.layout import game_patches_serializer
from randovania.layout.permalink import Permalink
from randovania.layout.preset_migration import VersionedPreset


@lru_cache(maxsize=1)
def _shareable_hash_words() -> Dict[RandovaniaGame, typing.List[str]]:
    with (get_data_path() / "hash_words" / "hash_words.json").open() as hash_words_file:
        return {
            RandovaniaGame(key): words
            for key, words in json.load(hash_words_file).items()
        }


CURRENT_DESCRIPTION_SCHEMA_VERSION = 6


def migrate_description(json_dict: dict) -> dict:
    if "schema_version" not in json_dict:
        raise ValueError(f"missing schema_version")

    version = json_dict["schema_version"]
    if version > CURRENT_DESCRIPTION_SCHEMA_VERSION:
        raise ValueError(f"Version {version} is newer than latest supported {CURRENT_DESCRIPTION_SCHEMA_VERSION}")

    if version == 1:
        for game in json_dict["game_modifications"]:
            for hint in game["hints"].values():
                if hint.get("precision") is not None:
                    owner = False
                    if hint["precision"]["item"] == "owner":
                        owner = True
                        hint["precision"]["item"] = "nothing"
                    hint["precision"]["include_owner"] = owner
        version += 1

    if version == 2:
        for game in json_dict["game_modifications"]:
            for hint in game["hints"].values():
                precision = hint.get("precision")
                if precision is not None and precision.get("relative") is not None:
                    precision["relative"]["distance_offset"] = 0
                    precision["relative"].pop("precise_distance")
        version += 1

    if version == 3:
        target_name_re = re.compile(r"(.*) for Player (\d+)")
        if len(json_dict["game_modifications"]) > 1:
            for game in json_dict["game_modifications"]:
                for area in game["locations"].values():
                    for location_name, contents in typing.cast(Dict[str, str], area).items():
                        m = target_name_re.match(contents)
                        if m is not None:
                            part_one, part_two = m.group(1, 2)
                            area[location_name] = f"{part_one} for Player {int(part_two) + 1}"
        version += 1

    if version == 4:
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

        version += 1

    if version == 5:
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

        for game in json_dict["game_modifications"]:
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

        version += 1

    json_dict["schema_version"] = version
    if version != CURRENT_DESCRIPTION_SCHEMA_VERSION:
        raise RuntimeError(f"Description migration did not end at current version")
    return json_dict


@dataclass(frozen=True)
class LayoutDescription:
    version: str
    permalink: Permalink
    all_patches: Dict[int, GamePatches]
    item_order: Tuple[str, ...]

    def __post_init__(self):
        object.__setattr__(self, "__cached_serialized_patches", None)

    @classmethod
    def file_extension(cls) -> str:
        return "rdvgame"

    @classmethod
    def from_json_dict(cls, json_dict: dict) -> "LayoutDescription":
        json_dict = migrate_description(json_dict)

        has_spoiler = "game_modifications" in json_dict
        if not has_spoiler:
            raise ValueError("Unable to read details of seed log with spoiler disabled")

        permalink = Permalink(
            seed_number=json_dict["info"]["seed"],
            spoiler=has_spoiler,
            presets={
                index: VersionedPreset(preset).get_preset()
                for index, preset in enumerate(json_dict["info"]["presets"])
            },
        )

        return LayoutDescription(
            version=json_dict["info"]["version"],
            permalink=permalink,
            all_patches=game_patches_serializer.decode(
                json_dict["game_modifications"], {
                    index: preset.configuration
                    for index, preset in permalink.presets.items()
                }),
            item_order=json_dict["item_order"],
        )

    @classmethod
    def from_file(cls, json_path: Path) -> "LayoutDescription":
        with json_path.open("r") as open_file:
            return cls.from_json_dict(json.load(open_file))

    def get_preset(self, player_index: int):
        return self.permalink.get_preset(player_index)

    @property
    def _serialized_patches(self):
        cached_result = object.__getattribute__(self, "__cached_serialized_patches")
        if cached_result is None:
            cached_result = game_patches_serializer.serialize(
                self.all_patches,
                {
                    index: preset.game
                    for index, preset in self.permalink.presets.items()
                })
            object.__setattr__(self, "__cached_serialized_patches", cached_result)

        return cached_result

    @property
    def as_json(self) -> dict:
        result = {
            "schema_version": CURRENT_DESCRIPTION_SCHEMA_VERSION,
            "info": {
                "version": self.version,
                "permalink": self.permalink.as_base64_str,
                "seed": self.permalink.seed_number,
                "hash": self.shareable_hash,
                "word_hash": self.shareable_word_hash,
                "presets": [
                    VersionedPreset.with_preset(preset).as_json
                    for preset in self.permalink.presets.values()
                ],
            }
        }

        if self.permalink.spoiler:
            result["game_modifications"] = self._serialized_patches
            result["item_order"] = self.item_order

        return result

    @property
    def all_games(self) -> typing.FrozenSet[RandovaniaGame]:
        return frozenset(preset.game for preset in self.permalink.presets.values())

    @property
    def _shareable_hash_bytes(self) -> bytes:
        bytes_representation = json.dumps(self._serialized_patches).encode()
        return hashlib.blake2b(bytes_representation, digest_size=5).digest()

    @property
    def shareable_hash(self) -> str:
        return base64.b32encode(self._shareable_hash_bytes).decode()

    @property
    def shareable_word_hash(self) -> str:
        rng = Random(sum([hash_byte * (2 ** 8) ** i for i, hash_byte in enumerate(self._shareable_hash_bytes)]))
        words = _shareable_hash_words()

        # We're not using self.all_games because we want multiple copies of a given game in the list,
        # so a game that has more players is more likely to have words in the hash
        all_games = [preset.game for preset in self.permalink.presets.values()]

        games_left = []
        selected_words = []
        for _ in range(3):
            if not games_left:
                games_left = list(all_games)
            selected_game = rng.choice(games_left)
            games_left = [game for game in games_left if game != selected_game]

            game_word_list = words.get(selected_game, [])
            if not game_word_list:
                game_word_list = list(itertools.chain.from_iterable(words.values()))
            selected_words.append(rng.choice(game_word_list))

        return " ".join(selected_words)

    def save_to_file(self, json_path: Path):
        with json_path.open("w") as open_file:
            json.dump(self.as_json, open_file, indent=4, separators=(',', ': '))

    @property
    def without_item_order(self) -> "LayoutDescription":
        """
        A solver path is way too big to reasonably store for test purposes, so use LayoutDescriptions with an empty one.
        :return:
        """
        return LayoutDescription(
            permalink=self.permalink,
            version=self.version,
            all_patches=self.all_patches,
            item_order=())
