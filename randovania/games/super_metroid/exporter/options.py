import dataclasses
from pathlib import Path

from randovania.games.game import RandovaniaGame
from randovania.interface_common.options import PerGameOptions, decode_if_not_none


@dataclasses.dataclass(frozen=True)
class SuperMetroidPerGameOptions(PerGameOptions):
    input_path: Path | None = None
    output_directory: Path | None = None
    output_format: str = "smc"

    @property
    def as_json(self):
        return {
            **super().as_json,
            "input_path": str(self.input_path) if self.input_path is not None else None,
            "output_directory": str(self.output_directory) if self.output_directory is not None else None,
            "output_format": self.output_format,
        }

    @classmethod
    def from_json(cls, value: dict) -> "SuperMetroidPerGameOptions":
        game = RandovaniaGame.SUPER_METROID
        cosmetic_patches = game.data.layout.cosmetic_patches.from_json(value["cosmetic_patches"])
        return cls(
            cosmetic_patches=cosmetic_patches,
            input_path=decode_if_not_none(value["input_path"], Path),
            output_directory=decode_if_not_none(value["output_directory"], Path),
            output_format=value["output_format"],
        )
