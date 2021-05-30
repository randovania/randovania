from dataclasses import dataclass

from randovania.game_description.world.area_location import AreaLocation


@dataclass(frozen=True, order=True)
class Teleporter:
    world_asset_id: int
    area_asset_id: int
    instance_id: int

    @property
    def as_json(self) -> dict:
        return {
            "world_asset_id": self.world_asset_id,
            "area_asset_id": self.area_asset_id,
            "instance_id": self.instance_id,
        }

    @classmethod
    def from_json(cls, value: dict) -> "Teleporter":
        return cls(value["world_asset_id"], value["area_asset_id"], value["instance_id"])

    def __repr__(self):
        return "world 0x{:02X}/area 0x{:02X}/instance 0x{:02X}".format(
            self.world_asset_id, self.area_asset_id, self.instance_id,
        )

    @property
    def area_location(self) -> AreaLocation:
        return AreaLocation(self.world_asset_id, self.area_asset_id)
