from __future__ import annotations


class InvalidConfiguration(Exception):
    def __init__(self, message: str, world_name: str | None = None):
        super().__init__(message)
        self.world_name = world_name
