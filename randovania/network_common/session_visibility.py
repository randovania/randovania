from __future__ import annotations

from enum import Enum


class MultiplayerSessionVisibility(Enum):
    """Visibility of a multiplayer session"""

    VISIBLE = "visible"
    HIDDEN = "hidden"

    @property
    def user_friendly_name(self) -> str:
        return self.name.title()
