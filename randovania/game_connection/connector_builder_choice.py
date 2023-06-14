from enum import Enum


class ConnectorBuilderChoice(Enum):
    DEBUG = "debug"
    DOLPHIN = "dolphin"
    NINTENDONT = "nintendont"
    DREAD = "dread"

    @property
    def pretty_text(self) -> str:
        return _pretty_backend_name[self]

    def supports_multiple_instances(self):
        return self == ConnectorBuilderChoice.NINTENDONT


_pretty_backend_name = {
    ConnectorBuilderChoice.DEBUG: "Debug",
    ConnectorBuilderChoice.DOLPHIN: "Dolphin",
    ConnectorBuilderChoice.NINTENDONT: "Nintendont",
    ConnectorBuilderChoice.DREAD: "Dread",
}
