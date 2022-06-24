from dataclasses import dataclass


@dataclass(frozen=True, order=True, slots=True)
class AreaIdentifier:
    world_name: str
    area_name: str

    def __post_init__(self):
        assert isinstance(self.world_name, str)
        assert isinstance(self.area_name, str)

    @property
    def as_json(self) -> dict:
        return {
            "world_name": self.world_name,
            "area_name": self.area_name,
        }

    @classmethod
    def from_json(cls, value: dict) -> "AreaIdentifier":
        try:
            return cls(value["world_name"], value["area_name"])
        except Exception:
            raise

    @property
    def as_tuple(self) -> tuple[str, str]:
        return self.world_name, self.area_name

    @property
    def as_string(self) -> str:
        return f"{self.world_name}/{self.area_name}"

    @classmethod
    def from_string(cls, value: str) -> "AreaIdentifier":
        return cls(*value.split("/", 1))

    def __repr__(self):
        return f"world {self.world_name}/area {self.area_name}"
