from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Self

from randovania.game.game_enum import RandovaniaGame
from randovania.interface_common.options import PerGameOptions, decode_if_not_none


@dataclasses.dataclass(frozen=True)
class FactorioPerGameOptions(PerGameOptions):
    """ """

    output_path: Path | None = None

    @property
    def as_json(self) -> dict:
        return {
            **super().as_json,
            "output_path": str(self.output_path) if self.output_path is not None else None,
        }

    @classmethod
    def from_json(cls, value: dict) -> Self:
        game = RandovaniaGame.FACTORIO
        cosmetic_patches = game.data.layout.cosmetic_patches.from_json(value["cosmetic_patches"])
        return cls(
            cosmetic_patches=cosmetic_patches,
            output_path=decode_if_not_none(value["output_path"], Path),
        )
