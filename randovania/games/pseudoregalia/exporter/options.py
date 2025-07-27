from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Self, override

from randovania.game.game_enum import RandovaniaGame
from randovania.interface_common.options import PerGameOptions, decode_if_not_none


@dataclasses.dataclass(frozen=True)
class PseudoregaliaPerGameOptions(PerGameOptions):
    """ """

    game_dir: Path | None = None

    @property
    def as_json(self) -> dict:
        return {
            **super().as_json,
            "game_dir": str(self.game_dir) if self.game_dir is not None else None,
        }

    @classmethod
    def from_json(cls, value: dict) -> Self:
        game = RandovaniaGame.PSEUDOREGALIA
        cosmetic_patches = game.data.layout.cosmetic_patches.from_json(value["cosmetic_patches"])
        return cls(
            cosmetic_patches=cosmetic_patches,
            game_dir=decode_if_not_none(value["game_dir"], Path),
        )

    @classmethod
    @override
    def game_enum(cls) -> RandovaniaGame:
        return RandovaniaGame.PSEUDOREGALIA
