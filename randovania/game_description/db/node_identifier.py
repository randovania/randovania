from __future__ import annotations

import dataclasses
from typing import Self

from randovania.game_description.db.area_identifier import AreaIdentifier


@dataclasses.dataclass(frozen=True, order=True, slots=True)
class NodeIdentifier:
    region: str
    area: str
    node: str

    @classmethod
    def create(cls, region: str, area: str, node: str) -> Self:
        return cls(region, area, node)

    @classmethod
    def with_area(cls, area_identifier: AreaIdentifier, node_name: str) -> Self:
        return cls(area_identifier.region, area_identifier.area, node_name)

    @property
    def as_json(self) -> dict:
        return {
            "region": self.region,
            "area": self.area,
            "node": self.node,
        }

    @classmethod
    def from_json(cls, value: dict) -> Self:
        return cls(value["region"], value["area"], value["node"])

    @property
    def as_string(self) -> str:
        return f"{self.region}/{self.area}/{self.node}"

    @classmethod
    def from_string(cls, value: str) -> Self:
        return cls.create(*value.split("/", 2))

    def __repr__(self) -> str:
        return f"region {self.region}/area {self.area}/node {self.node}"

    @property
    def area_identifier(self) -> AreaIdentifier:
        return AreaIdentifier(self.region, self.area)

    def renamed(self, new_name: str) -> NodeIdentifier:
        return NodeIdentifier(self.region, self.area, node=new_name)
