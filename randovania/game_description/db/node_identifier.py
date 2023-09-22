from __future__ import annotations

from typing import Self

import attrs

from randovania.game_description.db.area_identifier import AreaIdentifier


@attrs.define(init=True, frozen=True, cache_hash=True, order=True, slots=True)
class NodeIdentifier:
    area_identifier: AreaIdentifier
    node_name: str

    @classmethod
    def create(cls, region: str, area: str, node: str) -> Self:
        return cls(AreaIdentifier(region, area), node)

    @property
    def as_json(self) -> dict:
        result = self.area_identifier.as_json
        result["node"] = self.node_name
        return result

    @classmethod
    def from_json(cls, value: dict) -> Self:
        return cls(AreaIdentifier.from_json(value), value["node"])

    @property
    def as_string(self) -> str:
        return f"{self.region_name}/{self.area_name}/{self.node_name}"

    @classmethod
    def from_string(cls, value: str) -> Self:
        return cls.create(*value.split("/", 2))

    def __repr__(self) -> str:
        return f"{self.area_identifier}/node {self.node_name}"

    @property
    def region_name(self) -> str:
        return self.area_identifier.region_name

    @property
    def area_name(self) -> str:
        return self.area_identifier.area_name

    @property
    def area_location(self) -> AreaIdentifier:
        return self.area_identifier

    def renamed(self, new_name: str) -> NodeIdentifier:
        return NodeIdentifier(area_identifier=self.area_identifier, node_name=new_name)
