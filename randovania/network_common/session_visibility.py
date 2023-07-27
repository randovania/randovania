from __future__ import annotations

from enum import Enum


class MultiplayerSessionVisibility(Enum):
    """Visibility of a multiplayer session"""
    VISIBLE = "setup"
    HIDDEN = "finished"

    # This item still exists for support to old db values
    # The same applies for the enum values
    IN_PROGRESS = "in-progress"

    @property
    def user_friendly_name(self) -> str:
        return self.name.title()
