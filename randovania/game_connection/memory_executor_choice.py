# TODO: Rename the file. We don't select a MemoryExecutor anymore but a ConnectionBuilder
from enum import Enum


class ConnectorBuilderChoice(Enum):
    DOLPHIN = "dolphin"
    NINTENDONT = "nintendont"

    @property
    def pretty_text(self) -> str:
        return _pretty_backend_name[self]


_pretty_backend_name = {
    ConnectorBuilderChoice.DOLPHIN: "Dolphin",
    ConnectorBuilderChoice.NINTENDONT: "Nintendont",
}
