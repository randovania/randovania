from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Self

from randovania.games.game import RandovaniaGame
from randovania.interface_common.options import PerGameOptions, decode_if_not_none


@dataclasses.dataclass(frozen=True)
class BlankPerGameOptions(PerGameOptions):
    """ """

    input_path: Path | None = None
    output_path: Path | None = None

    @property
    def as_json(self) -> dict:
        return {
            **super().as_json,
            "input_path": str(self.input_path) if self.input_path is not None else None,
            "output_path": str(self.output_path) if self.output_path is not None else None,
        }

    @classmethod
    def from_json(cls, value: dict) -> Self:
        game = RandovaniaGame.BLANK
        cosmetic_patches = game.data.layout.cosmetic_patches.from_json(value["cosmetic_patches"])
        return cls(
            cosmetic_patches=cosmetic_patches,
            input_path=decode_if_not_none(value["input_path"], Path),
            output_path=decode_if_not_none(value["output_path"], Path),
        )
