from enum import Enum

from randovania.bitpacking.bitpacking import BitPackEnum


class LayoutTrickLevel(BitPackEnum, Enum):
    DISABLED = "disabled"
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"
    HYPERMODE = "hypermode"

    @classmethod
    def default(cls) -> "LayoutTrickLevel":
        return cls.DISABLED

    @classmethod
    def maximum(cls) -> "LayoutTrickLevel":
        return _TRICK_LEVEL_ORDER[-1]

    @classmethod
    def from_number(cls, number: int) -> "LayoutTrickLevel":
        return _TRICK_LEVEL_ORDER[number]

    @property
    def as_number(self) -> int:
        return _TRICK_LEVEL_ORDER.index(self)

    @property
    def long_name(self) -> str:
        return _PRETTY_TRICK_LEVEL_NAME[self]

    @property
    def is_enabled(self) -> bool:
        return self.as_number > LayoutTrickLevel.DISABLED.as_number


_TRICK_LEVEL_ORDER: list[LayoutTrickLevel] = list(LayoutTrickLevel)
_PRETTY_TRICK_LEVEL_NAME = {
    LayoutTrickLevel.DISABLED: "Disabled",
    LayoutTrickLevel.BEGINNER: "Beginner",
    LayoutTrickLevel.INTERMEDIATE: "Intermediate",
    LayoutTrickLevel.ADVANCED: "Advanced",
    LayoutTrickLevel.EXPERT: "Expert",
    LayoutTrickLevel.HYPERMODE: "Hypermode",
}
