from __future__ import annotations

from enum import Enum
from typing import Self

from randovania.bitpacking.bitpacking import BitPackEnum
from randovania.lib import enum_lib


class LayoutTrickLevel(BitPackEnum, Enum):
    long_name: str

    DISABLED = "disabled"
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"
    HYPERMODE = "hypermode"

    @classmethod
    def default(cls) -> Self:
        return cls.DISABLED

    @classmethod
    def maximum(cls) -> Self:
        return _TRICK_LEVEL_ORDER[-1]

    @classmethod
    def from_number(cls, number: int) -> Self:
        return _TRICK_LEVEL_ORDER[number]

    @property
    def as_number(self) -> int:
        return _TRICK_LEVEL_ORDER.index(self)

    @property
    def is_enabled(self) -> bool:
        return self.as_number > LayoutTrickLevel.DISABLED.as_number


_TRICK_LEVEL_ORDER: list[LayoutTrickLevel] = list(LayoutTrickLevel)
enum_lib.add_long_name(
    LayoutTrickLevel,
    {
        LayoutTrickLevel.DISABLED: "Disabled",
        LayoutTrickLevel.BEGINNER: "Beginner",
        LayoutTrickLevel.INTERMEDIATE: "Intermediate",
        LayoutTrickLevel.ADVANCED: "Advanced",
        LayoutTrickLevel.EXPERT: "Expert",
        LayoutTrickLevel.HYPERMODE: "Hypermode",
    },
)
