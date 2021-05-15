from enum import Enum


class TrackerTheme(Enum):
    CLASSIC = "classic"
    GAME = "game"

    @classmethod
    def default(cls) -> "TrackerTheme":
        return TrackerTheme.CLASSIC
