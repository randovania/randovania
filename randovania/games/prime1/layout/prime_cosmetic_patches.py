from __future__ import annotations

import dataclasses

from randovania.game.game_enum import RandovaniaGame
from randovania.games.prime1.layout.prime_user_preferences import PrimeUserPreferences
from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches

DEFAULT_HUD_COLOR = (102, 174, 225)


@dataclasses.dataclass(frozen=True)
class PrimeCosmeticPatches(BaseCosmeticPatches):
    open_map: bool = True
    pickup_markers: bool = True
    force_fusion: bool = False
    use_hud_color: bool = False
    hud_color: tuple[int, int, int] = DEFAULT_HUD_COLOR
    rainbow_phazon_ball: bool = False
    suit_color_rotations: tuple[int, int, int, int] = (0, 0, 0, 0)
    fusion_suit_color_rotations: tuple[int, int, int, int] = (0, 0, 0, 0)
    match_gunship_to_power_suit: bool = True
    gunship_color_rotation: int = 0
    user_preferences: PrimeUserPreferences = dataclasses.field(default_factory=PrimeUserPreferences)

    @classmethod
    def default(cls) -> PrimeCosmeticPatches:
        return cls()

    @classmethod
    def game(cls) -> RandovaniaGame:
        return RandovaniaGame.METROID_PRIME

    @property
    def active_suit_color_rotations(self) -> tuple[int, int, int, int]:
        """The rotations that apply to the suits the player will actually see."""
        return self.fusion_suit_color_rotations if self.force_fusion else self.suit_color_rotations

    @property
    def active_gunship_color_rotation(self) -> int | None:
        if self.force_fusion or not self.match_gunship_to_power_suit:
            return self.gunship_color_rotation
        return None  # Let randomprime default to Power Suit

    def __post_init__(self) -> None:
        if len(self.suit_color_rotations) != 4:
            raise ValueError("Suit color rotations must be a tuple of 4 ints.")
        if len(self.fusion_suit_color_rotations) != 4:
            raise ValueError("Fusion suit color rotations must be a tuple of 4 ints.")
        if len(self.hud_color) != 3:
            raise ValueError("HUD color must be a tuple of 3 ints.")
