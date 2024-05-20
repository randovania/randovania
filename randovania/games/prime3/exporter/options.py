from __future__ import annotations

import dataclasses
from typing import Self

from randovania.games.game import RandovaniaGame
from randovania.interface_common.options import PerGameOptions


@dataclasses.dataclass(frozen=True)
class CorruptionPerGameOptions(PerGameOptions):
    """ """

    @property
    def as_json(self) -> dict:
        return {
            **super().as_json,
        }

    @classmethod
    def from_json(cls, value: dict) -> Self:
        game = RandovaniaGame.METROID_PRIME_CORRUPTION
        cosmetic_patches = game.data.layout.cosmetic_patches.from_json(value["cosmetic_patches"])
        return cls(
            cosmetic_patches=cosmetic_patches,
        )
