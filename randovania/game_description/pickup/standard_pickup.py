import dataclasses
from dataclasses import dataclass
from typing import Self

from frozendict import frozendict

from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.game_description.pickup.pickup_category import PickupCategory
from randovania.game_description.resources.location_category import LocationCategory
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.game import RandovaniaGame

EXCLUDE_DEFAULT = {"exclude_if_default": True}


@dataclass(frozen=True)
class StandardPickupDefinition(JsonDataclass):
    game: RandovaniaGame = dataclasses.field(metadata={"init_from_extra": True})
    name: str = dataclasses.field(metadata={"init_from_extra": True})
    pickup_category: PickupCategory = dataclasses.field(metadata={"init_from_extra": True})
    broad_category: PickupCategory = dataclasses.field(metadata={"init_from_extra": True})
    model_name: str
    progression: tuple[str, ...]
    default_shuffled_count: int
    default_starting_count: int
    preferred_location_category: LocationCategory
    ammo: tuple[str, ...] = dataclasses.field(default_factory=tuple, metadata=EXCLUDE_DEFAULT)
    unlocks_ammo: bool = dataclasses.field(default=False, metadata=EXCLUDE_DEFAULT)
    additional_resources: frozendict[str, int] = dataclasses.field(default_factory=frozendict, metadata=EXCLUDE_DEFAULT)
    hide_from_gui: bool = dataclasses.field(default=False, metadata=EXCLUDE_DEFAULT)
    must_be_starting: bool = dataclasses.field(default=False, metadata=EXCLUDE_DEFAULT)
    original_location: PickupIndex | None = dataclasses.field(default=None, metadata=EXCLUDE_DEFAULT)
    probability_offset: int = dataclasses.field(default=0, metadata=EXCLUDE_DEFAULT)
    probability_multiplier: float = dataclasses.field(default=1.0, metadata=EXCLUDE_DEFAULT)
    description: str | None = dataclasses.field(default=None, metadata=EXCLUDE_DEFAULT)
    extra: frozendict = dataclasses.field(default_factory=frozendict, metadata=EXCLUDE_DEFAULT)

    def __post_init__(self):
        if not self.progression and not self.ammo:
            raise ValueError(f"Standard Pickup {self.name} has no progression nor ammo.")

    @classmethod
    def from_json_with_categories(cls, name: str, game: RandovaniaGame, pickup_categories: dict[str, PickupCategory],
                                  value: dict) -> Self:
        return cls.from_json(
            value,
            game=game,
            name=name,
            pickup_category=pickup_categories[value["pickup_category"]],
            broad_category=pickup_categories[value["broad_category"]],
        )

    @property
    def as_json(self) -> dict:
        return {
            "pickup_category": self.pickup_category.name,
            "broad_category": self.broad_category.name,
            **super().as_json,
        }
