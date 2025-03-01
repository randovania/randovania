from __future__ import annotations

from enum import Enum

import randovania


class DevelopmentState(Enum):
    """Indicates in which builds of Randovania a game is available in."""

    STABLE = "stable"
    """The game is available in stable builds, dev builds or when running RDV from source."""
    STAGING = "staging"
    """The game is available in dev-builds or when running RDV from source."""
    SOURCE_ONLY = "source"
    """Indicates that the game is only available when running RDV from source."""

    @property
    def is_stable(self) -> bool:
        return self == DevelopmentState.STABLE

    def can_view(self) -> bool:
        if self.is_stable:
            return True

        if self == DevelopmentState.STAGING:
            return randovania.is_dev_version()

        return not randovania.is_frozen()
