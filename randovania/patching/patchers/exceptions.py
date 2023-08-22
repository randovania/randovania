from __future__ import annotations


class UnableToExportError(Exception):
    """
    An exception that gets raised if a game export was unable to be performed due to user environment limitations.
    """

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason
