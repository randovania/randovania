import dataclasses
from pathlib import Path
from typing import Optional

from randovania.games.game import RandovaniaGame
from randovania.interface_common.options import PerGameOptions, decode_if_not_none


@dataclasses.dataclass(frozen=True)
class CSPerGameOptions(PerGameOptions):
    output_directory: Optional[Path] = None

    @property
    def as_json(self):
        return {
            **super().as_json,
            "output_directory": str(self.output_directory) if self.output_directory is not None else None,
        }

    @classmethod
    def from_json(cls, value: dict) -> "CSPerGameOptions":
        game = RandovaniaGame.CAVE_STORY
        cosmetic_patches = game.data.layout.cosmetic_patches.from_json(value["cosmetic_patches"])
        return cls(
            cosmetic_patches=cosmetic_patches,
            output_directory=decode_if_not_none(value["output_directory"], Path),
        )
