from enum import Enum


class ConnectorBuilderChoice(Enum):
    DOLPHIN = "dolphin"
    NINTENDONT = "nintendont"

    @property
    def pretty_text(self) -> str:
        return _pretty_backend_name[self]

    def supports_multiple_instances(self):
        return self == ConnectorBuilderChoice.NINTENDONT


_pretty_backend_name = {
    ConnectorBuilderChoice.DOLPHIN: "Dolphin",
    ConnectorBuilderChoice.NINTENDONT: "Nintendont",
}
