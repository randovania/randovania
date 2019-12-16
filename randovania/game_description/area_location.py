from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class AreaLocation:
    world_asset_id: int
    area_asset_id: int

    @property
    def as_json(self) -> dict:
        return {
            "world_asset_id": self.world_asset_id,
            "area_asset_id": self.area_asset_id,
        }

    @classmethod
    def from_json(cls, value: dict) -> "AreaLocation":
        return cls(value["world_asset_id"], value["area_asset_id"])

    def __repr__(self):
        return "world 0x{:02X}/area 0x{:02X}".format(self.world_asset_id, self.area_asset_id)
