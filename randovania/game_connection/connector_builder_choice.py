from __future__ import annotations

import os
import platform
from enum import Enum
from typing import Self

import randovania


class ConnectorBuilderChoice(Enum):
    AM2R = "am2r"
    CS = "cave-story"
    DEBUG = "debug"
    DOLPHIN = "dolphin"
    DREAD = "dread"
    NINTENDONT = "nintendont"
    MSR = "msr"

    @property
    def pretty_text(self) -> str:
        return _pretty_backend_name[self]

    def is_usable(self) -> bool:
        if self is ConnectorBuilderChoice.DEBUG:
            if randovania.is_frozen() or not randovania.is_dev_version():
                return False

        if self is ConnectorBuilderChoice.DOLPHIN:
            match platform.system():
                case "Darwin":
                    return False
                case "Linux" if randovania.is_frozen():
                    return os.getuid() == 0 and not randovania.is_flatpak()
                case _:
                    return True

        return True

    def supports_multiple_instances(self) -> bool:
        return self != ConnectorBuilderChoice.DOLPHIN

    @classmethod
    def all_usable_choices(cls) -> list[Self]:
        return [r for r in cls if r.is_usable()]


_pretty_backend_name = {
    ConnectorBuilderChoice.AM2R: "AM2R",
    ConnectorBuilderChoice.CS: "Cave Story",
    ConnectorBuilderChoice.DEBUG: "Debug",
    ConnectorBuilderChoice.DOLPHIN: "Dolphin",
    ConnectorBuilderChoice.DREAD: "Dread",
    ConnectorBuilderChoice.NINTENDONT: "Nintendont",
    ConnectorBuilderChoice.MSR: "Samus Returns",
}
