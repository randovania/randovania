from __future__ import annotations

import dataclasses
import uuid
from dataclasses import dataclass

INVALID_UUID = uuid.UUID("00000000-0000-1111-0000-000000000000")


@dataclass(frozen=True)
class PlayersConfiguration:
    player_index: int
    player_names: dict[int, str]
    uuids: dict[int, uuid.UUID] = dataclasses.field(default_factory=dict)
    session_name: str | None = None

    def get_own_name(self) -> str:
        return self.player_names[self.player_index]

    def get_own_uuid(self) -> uuid.UUID:
        return self.uuids.get(self.player_index, INVALID_UUID)

    @property
    def is_multiworld(self) -> int:
        return len(self.player_names) > 1
