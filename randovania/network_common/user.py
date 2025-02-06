from __future__ import annotations

import dataclasses

from randovania.bitpacking.json_dataclass import JsonDataclass

UserID = int


@dataclasses.dataclass(frozen=True)
class RandovaniaUser(JsonDataclass):
    id: UserID
    name: str


@dataclasses.dataclass(frozen=True)
class CurrentUser:
    id: UserID
    name: str
    discord_id: int | None = None

    @classmethod
    def from_json(cls, data) -> CurrentUser:
        return cls(
            id=data["id"],
            name=data["name"],
            discord_id=data.get("discord_id"),
        )

    @property
    def as_json(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "discord_id": self.discord_id,
        }
