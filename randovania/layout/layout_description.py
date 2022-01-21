import base64
import hashlib
import itertools
import json
import typing
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from random import Random
from typing import Tuple, Dict

from randovania import get_data_path
from randovania.game_description.game_patches import GamePatches
from randovania.games.game import RandovaniaGame
from randovania.layout import game_patches_serializer, description_migration
from randovania.layout.permalink import Permalink
from randovania.layout.generator_parameters import GeneratorParameters
from randovania.layout.preset import Preset
from randovania.layout.versioned_preset import VersionedPreset


@lru_cache(maxsize=1)
def _all_hash_words() -> Dict[RandovaniaGame, typing.List[str]]:
    with (get_data_path() / "hash_words" / "hash_words.json").open() as hash_words_file:
        return {
            RandovaniaGame(key): words
            for key, words in json.load(hash_words_file).items()
        }


def shareable_word_hash(hash_bytes: bytes, all_games: list[RandovaniaGame]):
    rng = Random(sum([hash_byte * (2 ** 8) ** i for i, hash_byte in enumerate(hash_bytes)]))
    words = _all_hash_words()

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


@dataclass(frozen=True)
class LayoutDescription:
    version: str
    generator_parameters: GeneratorParameters
    all_patches: Dict[int, GamePatches]
    item_order: Tuple[str, ...]

    def __post_init__(self):
        object.__setattr__(self, "__cached_serialized_patches", None)

    @classmethod
    def file_extension(cls) -> str:
        return "rdvgame"

    @classmethod
    def from_json_dict(cls, json_dict: dict) -> "LayoutDescription":
        json_dict = description_migration.convert_to_current_version(json_dict)

        has_spoiler = "game_modifications" in json_dict
        if not has_spoiler:
            raise ValueError("Unable to read details of seed log with spoiler disabled")

        generator_parameters = GeneratorParameters(
            seed_number=json_dict["info"]["seed"],
            spoiler=has_spoiler,
            presets={
                index: VersionedPreset(preset).get_preset()
                for index, preset in enumerate(json_dict["info"]["presets"])
            },
        )

        return LayoutDescription(
            version=json_dict["info"]["version"],
            generator_parameters=generator_parameters,
            all_patches=game_patches_serializer.decode(
                json_dict["game_modifications"], {
                    index: preset.configuration
                    for index, preset in generator_parameters.presets.items()
                }),
            item_order=json_dict["item_order"],
        )

    @classmethod
    def from_file(cls, json_path: Path) -> "LayoutDescription":
        with json_path.open("r") as open_file:
            return cls.from_json_dict(json.load(open_file))

    @property
    def permalink(self):
        return Permalink(
            parameters=self.generator_parameters,
            seed_hash=self.shareable_hash_bytes,
            version=0,
        )

    @property
    def player_count(self) -> int:
        return self.generator_parameters.player_count

    def get_preset(self, player_index: int) -> Preset:
        return self.generator_parameters.get_preset(player_index)

    def get_seed_for_player(self, player_index: int) -> int:
        return self.generator_parameters.seed_number + player_index

    @property
    def _serialized_patches(self):
        cached_result = object.__getattribute__(self, "__cached_serialized_patches")
        if cached_result is None:
            cached_result = game_patches_serializer.serialize(
                self.all_patches,
                {
                    index: preset.game
                    for index, preset in self.generator_parameters.presets.items()
                })
            object.__setattr__(self, "__cached_serialized_patches", cached_result)

        return cached_result

    @property
    def as_json(self) -> dict:
        result = {
            "schema_version": description_migration.CURRENT_VERSION,
            "info": {
                "version": self.version,
                "permalink": self.permalink.as_base64_str,
                "seed": self.generator_parameters.seed_number,
                "hash": self.shareable_hash,
                "word_hash": self.shareable_word_hash,
                "presets": [
                    VersionedPreset.with_preset(preset).as_json
                    for preset in self.generator_parameters.presets.values()
                ],
            }
        }

        if self.generator_parameters.spoiler:
            result["game_modifications"] = self._serialized_patches
            result["item_order"] = self.item_order

        return result

    @property
    def all_games(self) -> typing.FrozenSet[RandovaniaGame]:
        return frozenset(preset.game for preset in self.generator_parameters.presets.values())

    @property
    def shareable_hash_bytes(self) -> bytes:
        bytes_representation = json.dumps(self._serialized_patches).encode()
        return hashlib.blake2b(bytes_representation, digest_size=5).digest()

    @property
    def shareable_hash(self) -> str:
        return base64.b32encode(self.shareable_hash_bytes).decode()

    @property
    def shareable_word_hash(self) -> str:
        # We're not using self.all_games because we want multiple copies of a given game in the list,
        # so a game that has more players is more likely to have words in the hash
        all_games = [preset.game for preset in self.generator_parameters.presets.values()]

        return shareable_word_hash(
            self.shareable_hash_bytes,
            all_games,
        )

    def save_to_file(self, json_path: Path):
        with json_path.open("w") as open_file:
            json.dump(self.as_json, open_file, indent=4, separators=(',', ': '))
