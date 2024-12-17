from __future__ import annotations

import dataclasses
from pathlib import Path

from randovania.game.game_enum import RandovaniaGame
from randovania.games.samus_returns.exporter.game_exporter import MSRModPlatform
from randovania.interface_common.options import PerGameOptions, decode_if_not_none


@dataclasses.dataclass(frozen=True)
class MSRPerGameOptions(PerGameOptions):
    input_file: Path | None = None
    target_platform: MSRModPlatform = MSRModPlatform.CITRA
    output_preference: str | None = None

    @property
    def as_json(self) -> dict:
        return {
            **super().as_json,
            "input_file": str(self.input_file) if self.input_file is not None else None,
            "target_platform": self.target_platform.value,
            "output_preference": self.output_preference,
        }

    @classmethod
    def from_json(cls, value: dict) -> MSRPerGameOptions:
        game = RandovaniaGame.METROID_SAMUS_RETURNS
        cosmetic_patches = game.data.layout.cosmetic_patches.from_json(value["cosmetic_patches"])
        return cls(
            cosmetic_patches=cosmetic_patches,
            input_file=decode_if_not_none(value["input_file"], Path),
            target_platform=MSRModPlatform(value["target_platform"]),
            output_preference=value["output_preference"],
        )
