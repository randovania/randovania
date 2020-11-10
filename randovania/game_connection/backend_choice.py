from enum import Enum


class GameBackendChoice(Enum):
    DOLPHIN = "dolphin"
    NINTENDONT = "nintendont"

    @property
    def pretty_text(self) -> str:
        return _pretty_backend_name[self]


_pretty_backend_name = {
    GameBackendChoice.DOLPHIN: "Dolphin",
    GameBackendChoice.NINTENDONT: "Nintendont",
}