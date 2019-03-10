from dataclasses import dataclass


@dataclass(frozen=True)
class AmmoState:
    variance: int
    pickup_count: int

    @property
    def as_json(self) -> dict:
        return {
            "variance": self.variance,
            "pickup_count": self.pickup_count,
        }

    @classmethod
    def from_json(cls, value: dict) -> "AmmoState":
        return cls(
            variance=value["variance"],
            pickup_count=value["pickup_count"],
        )
