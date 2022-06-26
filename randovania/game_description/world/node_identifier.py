import attrs

from randovania.game_description.world.area_identifier import AreaIdentifier


@attrs.define(init=True, frozen=True, cache_hash=True, order=True, slots=True)
class NodeIdentifier:
    area_identifier: AreaIdentifier
    node_name: str

    @classmethod
    def create(cls, world_name: str, area_name: str, node_name: str) -> "NodeIdentifier":
        return cls(AreaIdentifier(world_name, area_name), node_name)

    @property
    def as_json(self) -> dict:
        result = self.area_identifier.as_json
        result["node_name"] = self.node_name
        return result

    @classmethod
    def from_json(cls, value: dict) -> "NodeIdentifier":
        return cls(AreaIdentifier.from_json(value), value["node_name"])

    @property
    def as_string(self) -> str:
        return f"{self.world_name}/{self.area_name}/{self.node_name}"

    @classmethod
    def from_string(cls, value: str) -> "NodeIdentifier":
        return cls.create(*value.split("/", 2))

    def __repr__(self):
        return "{}/node {}".format(
            self.area_identifier, self.node_name,
        )

    @property
    def world_name(self) -> str:
        return self.area_identifier.world_name

    @property
    def area_name(self) -> str:
        return self.area_identifier.area_name

    @property
    def area_location(self) -> AreaIdentifier:
        return self.area_identifier

    def renamed(self, new_name: str) -> "NodeIdentifier":
        return NodeIdentifier(area_identifier=self.area_identifier, node_name=new_name)
