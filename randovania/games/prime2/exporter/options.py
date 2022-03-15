import dataclasses
from enum import Enum
from pathlib import Path
from typing import Optional

from randovania.games.game import RandovaniaGame
from randovania.interface_common.options import PerGameOptions, decode_if_not_none


@dataclasses.dataclass(frozen=True)
class EchoesPerGameOptions(PerGameOptions):
    input_path: Optional[Path] = None
    output_directory: Optional[Path] = None
    use_external_models: set[RandovaniaGame] = dataclasses.field(default_factory=set)

    @property
    def as_json(self):
        return {
            **super().as_json,
            "input_path": str(self.input_path) if self.input_path is not None else None,
            "output_directory": str(self.output_directory) if self.output_directory is not None else None,
            "use_external_models": [game.value for game in self.use_external_models]
        }

    @classmethod
    def from_json(cls, value: dict) -> "EchoesPerGameOptions":
        game = RandovaniaGame.METROID_PRIME_ECHOES
        cosmetic_patches = game.data.layout.cosmetic_patches.from_json(value["cosmetic_patches"])
        return cls(
            cosmetic_patches=cosmetic_patches,
            input_path=decode_if_not_none(value["input_path"], Path),
            output_directory=decode_if_not_none(value["output_directory"], Path),
            use_external_models={RandovaniaGame(g) for g in value["use_external_models"]},
        )
