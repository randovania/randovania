import dataclasses
from pathlib import Path
from typing import Optional

from randovania.games.dread.exporter.game_exporter import DreadModPlatform
from randovania.games.game import RandovaniaGame
from randovania.interface_common.options import PerGameOptions, decode_if_not_none


@dataclasses.dataclass(frozen=True)
class DreadPerGameOptions(PerGameOptions):
    input_directory: Optional[Path] = None
    target_platform: DreadModPlatform = DreadModPlatform.RYUJINX
    reduce_mod_size: bool = False
    output_preference: Optional[str] = None

    @property
    def as_json(self):
        return {
            **super().as_json,
            "input_directory": str(self.input_directory) if self.input_directory is not None else None,
            "target_platform": self.target_platform.value,
            "reduce_mod_size": self.reduce_mod_size,
            "output_preference": self.output_preference,
        }

    @classmethod
    def from_json(cls, value: dict) -> "DreadPerGameOptions":
        game = RandovaniaGame.METROID_DREAD
        cosmetic_patches = game.data.layout.cosmetic_patches.from_json(value["cosmetic_patches"])
        return cls(
            cosmetic_patches=cosmetic_patches,
            input_directory=decode_if_not_none(value["input_directory"], Path),
            target_platform=DreadModPlatform(value["target_platform"]),
            reduce_mod_size=value["reduce_mod_size"],
            output_preference=value["output_preference"],
        )
