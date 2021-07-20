from enum import Enum


class MemoryExecutorChoice(Enum):
    DOLPHIN = "dolphin"
    NINTENDONT = "nintendont"

    @property
    def pretty_text(self) -> str:
        return _pretty_backend_name[self]


_pretty_backend_name = {
    MemoryExecutorChoice.DOLPHIN: "Dolphin",
    MemoryExecutorChoice.NINTENDONT: "Nintendont",
}
