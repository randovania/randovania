import platform
from enum import Enum
from typing import Self

import randovania


class ConnectorBuilderChoice(Enum):
    DEBUG = "debug"
    DOLPHIN = "dolphin"
    NINTENDONT = "nintendont"
    DREAD = "dread"

    @property
    def pretty_text(self) -> str:
        return _pretty_backend_name[self]

    def is_usable(self) -> bool:
        if self is ConnectorBuilderChoice.DEBUG:
            if randovania.is_frozen() or not randovania.is_dev_version():
                return False

        if self is ConnectorBuilderChoice.DOLPHIN and platform.system() == "Darwin":
            return False

        return True

    def supports_multiple_instances(self) -> bool:
        return self != ConnectorBuilderChoice.DOLPHIN

    @classmethod
    def all_usable_choices(cls) -> list[Self]:
        return [
            r for r in cls
            if r.is_usable()
        ]


_pretty_backend_name = {
    ConnectorBuilderChoice.DEBUG: "Debug",
    ConnectorBuilderChoice.DOLPHIN: "Dolphin",
    ConnectorBuilderChoice.NINTENDONT: "Nintendont",
    ConnectorBuilderChoice.DREAD: "Dread",
}
