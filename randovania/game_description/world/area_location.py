from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class AreaLocation:
    world_name: str
    area_name: str

    @property
    def world_asset_id(self) -> int:
        raise KeyError("Should be using world_name")

    @property
    def area_asset_id(self) -> int:
        raise KeyError("Should be using area_name")

    @property
    def as_json(self) -> dict:
        return {
            "world_name": self.world_name,
            "area_name": self.area_name,
        }

    @classmethod
    def from_json(cls, value: dict) -> "AreaLocation":
        return cls(value["world_name"], value["area_name"])

    def __repr__(self):
        return "world {}/area {}".format(self.world_name, self.area_name)
