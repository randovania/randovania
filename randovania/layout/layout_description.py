import base64
import hashlib
import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from random import Random
from typing import NamedTuple, Tuple, List

from randovania import get_data_path
from randovania.game_description.game_patches import GamePatches
from randovania.layout import game_patches_serializer
from randovania.layout.permalink import Permalink


class SolverPath(NamedTuple):
    node_name: str
    previous_nodes: Tuple[str, ...]


def _playthrough_list_to_solver_path(playthrough: List[dict]) -> Tuple[SolverPath, ...]:
    return tuple(
        SolverPath(
            node_name=step["node"],
            previous_nodes=tuple(step["path_from_previous"])
        )
        for step in playthrough
    )


@lru_cache(maxsize=1)
def _shareable_hash_words():
    with (get_data_path() / "hash_words" / "hash_words.json").open() as hash_words_file:
        return json.load(hash_words_file)


@dataclass(frozen=True)
class LayoutDescription:
    version: str
    permalink: Permalink
    patches: GamePatches
    solver_path: Tuple[SolverPath, ...]

    @classmethod
    def file_extension(cls) -> str:
        return "rdvgame"

    @classmethod
    def from_json_dict(cls, json_dict: dict) -> "LayoutDescription":
        version = json_dict["info"]["version"]
        # version_as_obj = StrictVersion(version)
        #
        # if version_as_obj < StrictVersion("0.26.0"):
        #     raise RuntimeError("Unsupported log file version '{}'.".format(version))

        # TODO: add try/catch to throw convert potential errors in "seed from future version broke"
        permalink = Permalink.from_json_dict(json_dict["info"]["permalink"])

        if not permalink.spoiler:
            raise ValueError("Unable to read details of seed log with spoiler disabled")

        return LayoutDescription(
            version=version,
            permalink=permalink,
            patches=game_patches_serializer.decode(json_dict["game_modifications"], permalink.layout_configuration),
            solver_path=_playthrough_list_to_solver_path(json_dict["playthrough"]),
        )

    @classmethod
    def from_file(cls, json_path: Path) -> "LayoutDescription":
        with json_path.open("r") as open_file:
            return cls.from_json_dict(json.load(open_file))

    @property
    def as_json(self) -> dict:
        result = {
            "info": {
                "version": self.version,
                "permalink": self.permalink.as_json,
            }
        }

        if self.permalink.spoiler:
            result["game_modifications"] = game_patches_serializer.serialize(
                self.patches, self.permalink.layout_configuration.game_data)

            result["playthrough"] = [
                {
                    "path_from_previous": path.previous_nodes,
                    "node": path.node_name,
                }
                for path in self.solver_path
            ]

        return result

    @property
    def _shareable_hash_bytes(self) -> bytes:
        dict_to_serialize = game_patches_serializer.serialize(self.patches,
                                                              self.permalink.layout_configuration.game_data)
        bytes_representation = json.dumps(dict_to_serialize).encode()
        return hashlib.blake2b(bytes_representation, digest_size=5).digest()

    @property
    def shareable_hash(self) -> str:
        return base64.b32encode(self._shareable_hash_bytes).decode()

    @property
    def shareable_word_hash(self) -> str:
        rng = Random(sum([hash_byte * (2 ** 8) ** i for i, hash_byte in enumerate(self._shareable_hash_bytes)]))
        return " ".join(rng.sample(_shareable_hash_words(), 3))

    def save_to_file(self, json_path: Path):
        with json_path.open("w") as open_file:
            json.dump(self.as_json, open_file, indent=4, separators=(',', ': '))

    @property
    def without_solver_path(self) -> "LayoutDescription":
        """
        A solver path is way too big to reasonably store for test purposes, so use LayoutDescriptions with an empty one.
        :return:
        """
        return LayoutDescription(
            permalink=self.permalink,
            version=self.version,
            patches=self.patches,
            solver_path=())
