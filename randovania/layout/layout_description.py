import base64
import hashlib
import json
from dataclasses import dataclass
from distutils.version import StrictVersion
from pathlib import Path
from typing import NamedTuple, Tuple, List

from randovania.layout import game_patches_serializer
from randovania.game_description.game_patches import GamePatches
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


@dataclass(frozen=True)
class LayoutDescription:
    version: str
    permalink: Permalink
    patches: GamePatches
    solver_path: Tuple[SolverPath, ...]

    @classmethod
    def from_json_dict(cls, json_dict: dict) -> "LayoutDescription":
        version = json_dict["info"]["version"]
        version_as_obj = StrictVersion(version)

        if version_as_obj < StrictVersion("0.24.0"):
            raise RuntimeError("Unsupported log file version '{}'.".format(version))

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
    def shareable_hash(self) -> str:
        dict_to_serialize = game_patches_serializer.serialize(self.patches,
                                                              self.permalink.layout_configuration.game_data)
        bytes_representation = json.dumps(dict_to_serialize).encode()
        hashed_bytes = hashlib.blake2b(bytes_representation, digest_size=5).digest()
        return base64.b32encode(hashed_bytes).decode()

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
