from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class MajorItemState:
    include_copy_in_original_location: bool
    num_shuffled_pickups: int
    num_included_in_starting_items: int
    included_ammo: Tuple[int, ...]

    @property
    def as_json(self) -> dict:
        return {
            "include_copy_in_original_location": self.include_copy_in_original_location,
            "num_shuffled_pickups": self.num_shuffled_pickups,
            "num_included_in_starting_items": self.num_included_in_starting_items,
            "included_ammo": list(self.included_ammo),
        }

    @classmethod
    def from_json(cls, value: dict) -> "MajorItemState":
        return cls(
            include_copy_in_original_location=value["include_copy_in_original_location"],
            num_shuffled_pickups=value["num_shuffled_pickups"],
            num_included_in_starting_items=value["num_included_in_starting_items"],
            included_ammo=tuple(value["included_ammo"]),
        )
