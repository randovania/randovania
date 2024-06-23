from __future__ import annotations

import dataclasses
from pathlib import Path

from randovania.games.game import RandovaniaGame
from randovania.games.samus_returns.exporter.game_exporter import MSRGameVersion, MSRModPlatform
from randovania.interface_common.options import PerGameOptions, decode_if_not_none


@dataclasses.dataclass(frozen=True)
class MSRPerGameOptions(PerGameOptions):
    input_directory: Path | None = None
    input_exheader: Path | None = None
    target_platform: MSRModPlatform = MSRModPlatform.CITRA
    target_version: MSRGameVersion = MSRGameVersion.NTSC
    output_preference: str | None = None

    @property
    def as_json(self) -> dict:
        return {
            **super().as_json,
            "input_directory": str(self.input_directory) if self.input_directory is not None else None,
            "input_exheader": str(self.input_exheader) if self.input_exheader is not None else None,
            "target_platform": self.target_platform.value,
            "target_version": self.target_version.value,
            "output_preference": self.output_preference,
        }

    @classmethod
    def from_json(cls, value: dict) -> MSRPerGameOptions:
        game = RandovaniaGame.METROID_SAMUS_RETURNS
        cosmetic_patches = game.data.layout.cosmetic_patches.from_json(value["cosmetic_patches"])
        return cls(
            cosmetic_patches=cosmetic_patches,
            input_directory=decode_if_not_none(value["input_directory"], Path),
            input_exheader=decode_if_not_none(value["input_exheader"], Path),
            target_platform=MSRModPlatform(value["target_platform"]),
            target_version=MSRGameVersion(value["target_version"]),
            output_preference=value["output_preference"],
        )
