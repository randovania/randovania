from enum import Enum


class MultiplayerSessionState(Enum):
    """State of a game session"""
    SETUP = "setup"
    IN_PROGRESS = "in-progress"
    FINISHED = "finished"

    @property
    def user_friendly_name(self) -> str:
        return self.value.title()
