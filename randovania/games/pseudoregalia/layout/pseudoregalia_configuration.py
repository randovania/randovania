from __future__ import annotations

import dataclasses

from randovania.game.game_enum import RandovaniaGame
from randovania.layout.base.base_configuration import BaseConfiguration


@dataclasses.dataclass(frozen=True)
class PseudoregaliaConfiguration(BaseConfiguration):
    required_keys: int = dataclasses.field(metadata={"min": 0, "max": 5, "precision": 1})
    goatling_shuffle: bool
    chair_shuffle: bool
    note_shuffle: bool

    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        return RandovaniaGame.PSEUDOREGALIA

    def active_layers(self) -> set[str]:
        result = super().active_layers()

        if self.goatling_shuffle:
            result.add("goatling_shuffle")
        if self.chair_shuffle:
            result.add("chair_shuffle")
        if self.note_shuffle:
            result.add("note_shuffle")

        return result
