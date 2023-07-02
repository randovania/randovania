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
from randovania.game_description.game_patches import GamePatches
from randovania.games.game import RandovaniaGame
from randovania.layout import game_patches_serializer, description_migration
from randovania.layout.generator_parameters import GeneratorParameters
from randovania.layout.permalink import Permalink
from randovania.layout.preset import Preset
from randovania.layout.versioned_preset import VersionedPreset, InvalidPreset
from randovania.lib import obfuscator, json_lib


class InvalidLayoutDescription(Exception):
    pass


@lru_cache(maxsize=1)
def _all_hash_words() -> list[str]:
    return list(itertools.chain.from_iterable(
        game.hash_words for game in RandovaniaGame
        if game.hash_words is not None
    ))


def shareable_hash(hash_bytes: bytes) -> str:
    return base64.b32encode(hash_bytes).decode()


def shareable_word_hash(hash_bytes: bytes, all_games: list[RandovaniaGame]):
    rng = Random(sum(hash_byte * (2 ** 8) ** i for i, hash_byte in enumerate(hash_bytes)))

    games_left = []
    selected_words = []
    for _ in range(3):
        if not games_left:
            games_left = list(all_games)
        selected_game = rng.choice(games_left)
        games_left = [game for game in games_left if game != selected_game]

        game_word_list = _all_hash_words()
        if selected_game.hash_words is not None:
            game_word_list = selected_game.hash_words
        selected_words.append(rng.choice(game_word_list))

    return " ".join(selected_words)


def _info_hash(data: dict) -> str:
    bytes_representation = json.dumps(data).encode()
    return hashlib.blake2b(bytes_representation).hexdigest()


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
                   ) -> typing.Self:
        return cls(
            randovania_version_text=randovania.VERSION,
            randovania_version_git=randovania.GIT_HASH,
            generator_parameters=generator_parameters,
            all_patches=all_patches,
            item_order=item_order,
        )

    @classmethod
    def from_json_dict(cls, json_dict: dict) -> typing.Self:
        json_dict = description_migration.convert_to_current_version(json_dict)

        if "secret" in json_dict:
            try:
                secret = obfuscator.deobfuscate_json(json_dict["secret"])
                if _info_hash(json_dict["info"]) == secret.pop("info_hash"):
                    for key, value in secret.items():
                        json_dict[key] = value
            except (obfuscator.MissingSecret, obfuscator.InvalidSecret):
                pass

        if "game_modifications" not in json_dict:
            raise InvalidLayoutDescription("Unable to read details of a race game file")

        def get_preset(i, p):
            try:
                return VersionedPreset(p).get_preset()
            except InvalidPreset as e:
                raise InvalidLayoutDescription(
                    f"Invalid preset for world {i + 1}: {e}"
                ) from e.original_exception

        generator_parameters = GeneratorParameters(
            seed_number=json_dict["info"]["seed"],
            spoiler=json_dict["info"]["has_spoiler"],
            presets=[
                get_preset(i, preset)
                for i, preset in enumerate(json_dict["info"]["presets"])
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
    def from_file(cls, path: Path) -> typing.Self:
        return cls.from_json_dict(json_lib.read_path(path))

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

        spoiler = {
            "game_modifications": self._serialized_patches,
            "item_order": self.item_order,
        }
        if self.has_spoiler or force_spoiler:
            for k, v in spoiler.items():
                result[k] = v
        else:
            spoiler["info_hash"] = _info_hash(result["info"])
            try:
                result["secret"] = obfuscator.obfuscate_json(spoiler)
            except obfuscator.MissingSecret:
                pass

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
        json_lib.write_path(
            json_path, self.as_json()
        )
