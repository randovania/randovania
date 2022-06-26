import base64
import hashlib
import itertools
import json
import typing
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from random import Random

import randovania
from randovania import get_data_path
from randovania.game_description.game_patches import GamePatches
from randovania.games.game import RandovaniaGame
from randovania.layout import game_patches_serializer, description_migration
from randovania.layout.generator_parameters import GeneratorParameters
from randovania.layout.permalink import Permalink
from randovania.layout.preset import Preset
from randovania.layout.versioned_preset import VersionedPreset


@lru_cache(maxsize=1)
def _all_hash_words() -> dict[RandovaniaGame, list[str]]:
    with (get_data_path() / "hash_words" / "hash_words.json").open() as hash_words_file:
        return {
            RandovaniaGame(key): words
            for key, words in json.load(hash_words_file).items()
        }


def shareable_hash(hash_bytes: bytes) -> str:
    return base64.b32encode(hash_bytes).decode()


def shareable_word_hash(hash_bytes: bytes, all_games: list[RandovaniaGame]):
    rng = Random(sum(hash_byte * (2 ** 8) ** i for i, hash_byte in enumerate(hash_bytes)))
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
    randovania_version_text: str
    randovania_version_git: bytes
    generator_parameters: GeneratorParameters
    all_patches: dict[int, GamePatches]
    item_order: tuple[str, ...]

    def __post_init__(self):
        object.__setattr__(self, "__cached_serialized_patches", None)

    @classmethod
    def file_extension(cls) -> str:
        return "rdvgame"

    @classmethod
    def create_new(cls,
                   generator_parameters: GeneratorParameters,
                   all_patches: dict[int, GamePatches],
                   item_order: tuple[str, ...],
                   ) -> "LayoutDescription":
        return cls(
            randovania_version_text=randovania.VERSION,
            randovania_version_git=randovania.GIT_HASH,
            generator_parameters=generator_parameters,
            all_patches=all_patches,
            item_order=item_order,
        )

    @classmethod
    def from_json_dict(cls, json_dict: dict) -> "LayoutDescription":
        json_dict = description_migration.convert_to_current_version(json_dict)

        if "game_modifications" not in json_dict:
            raise ValueError("Unable to read details of a race game file")

        generator_parameters = GeneratorParameters(
            seed_number=json_dict["info"]["seed"],
            spoiler=json_dict["info"]["has_spoiler"],
            presets=[
                VersionedPreset(preset).get_preset()
                for preset in json_dict["info"]["presets"]
            ],
        )

        return LayoutDescription(
            randovania_version_text=json_dict["info"]["randovania_version"],
            randovania_version_git=bytes.fromhex(json_dict["info"]["randovania_version_git"]),
            generator_parameters=generator_parameters,
            all_patches=game_patches_serializer.decode(
                json_dict["game_modifications"], {
                    index: preset.configuration
                    for index, preset in enumerate(generator_parameters.presets)
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
            randovania_version=self.randovania_version_git,
        )

    @property
    def has_spoiler(self) -> bool:
        return self.generator_parameters.spoiler

    @property
    def player_count(self) -> int:
        return self.generator_parameters.player_count

    @property
    def all_presets(self) -> typing.Iterable[Preset]:
        return self.generator_parameters.presets

    def get_preset(self, player_index: int) -> Preset:
        return self.generator_parameters.get_preset(player_index)

    def get_seed_for_player(self, player_index: int) -> int:
        return self.generator_parameters.seed_number + player_index

    @property
    def _serialized_patches(self):
        cached_result = object.__getattribute__(self, "__cached_serialized_patches")
        if cached_result is None:
            cached_result = game_patches_serializer.serialize(self.all_patches)
            object.__setattr__(self, "__cached_serialized_patches", cached_result)

        return cached_result

    def as_json(self, *, force_spoiler: bool = False) -> dict:
        result = {
            "schema_version": description_migration.CURRENT_VERSION,
            "info": {
                "randovania_version": self.randovania_version_text,
                "randovania_version_git": self.randovania_version_git.hex(),
                "permalink": self.permalink.as_base64_str,
                "has_spoiler": self.has_spoiler,
                "seed": self.generator_parameters.seed_number,
                "hash": self.shareable_hash,
                "word_hash": self.shareable_word_hash,
                "presets": [
                    VersionedPreset.with_preset(preset).as_json
                    for preset in self.all_presets
                ],
            }
        }

        if self.has_spoiler or force_spoiler:
            result["game_modifications"] = self._serialized_patches
            result["item_order"] = self.item_order

        return result

    @property
    def all_games(self) -> frozenset[RandovaniaGame]:
        return frozenset(preset.game for preset in self.all_presets)

    @property
    def shareable_hash_bytes(self) -> bytes:
        bytes_representation = json.dumps(self._serialized_patches).encode()
        return hashlib.blake2b(bytes_representation, digest_size=5).digest()

    @property
    def shareable_hash(self) -> str:
        return shareable_hash(self.shareable_hash_bytes)

    @property
    def shareable_word_hash(self) -> str:
        # We're not using self.all_games because we want multiple copies of a given game in the list,
        # so a game that has more players is more likely to have words in the hash
        all_games = [preset.game for preset in self.all_presets]

        return shareable_word_hash(
            self.shareable_hash_bytes,
            all_games,
        )

    def save_to_file(self, json_path: Path):
        with json_path.open("w") as open_file:
            json.dump(self.as_json(), open_file, indent=4, separators=(',', ': '))
