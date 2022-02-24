import dataclasses
from pathlib import Path
from typing import Optional

from randovania.games.dread.exporter.game_exporter import DreadModFormat
from randovania.games.game import RandovaniaGame
from randovania.interface_common.options import PerGameOptions, decode_if_not_none


@dataclasses.dataclass(frozen=True)
class DreadPerGameOptions(PerGameOptions):
    input_directory: Optional[Path] = None
    output_directory: Optional[Path] = None
    output_format: DreadModFormat = DreadModFormat.RYUJINX
    output_to_ryujinx: bool = True

    @property
    def as_json(self):
        return {
            **super().as_json,
            "input_directory": str(self.input_directory) if self.input_directory is not None else None,
            "output_directory": str(self.output_directory) if self.output_directory is not None else None,
            "output_format": self.output_format.value,
            "output_to_ryujinx": self.output_to_ryujinx,
        }

    @classmethod
    def from_json(cls, value: dict) -> "DreadPerGameOptions":
        game = RandovaniaGame.METROID_DREAD
        cosmetic_patches = game.data.layout.cosmetic_patches.from_json(value["cosmetic_patches"])
        return cls(
            cosmetic_patches=cosmetic_patches,
            input_directory=decode_if_not_none(value["input_directory"], Path),
            output_directory=decode_if_not_none(value["output_directory"], Path),
            output_format=DreadModFormat(value["output_format"]),
            output_to_ryujinx=value["output_to_ryujinx"],
        )
