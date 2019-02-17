from dataclasses import dataclass


@dataclass(frozen=True)
class AmmoState:
    total_count: int
    variance: int
    pickup_count: int

    @property
    def as_json(self) -> dict:
        return {
            "total_count": self.total_count,
            "variance": self.variance,
            "pickup_count": self.pickup_count,
        }
