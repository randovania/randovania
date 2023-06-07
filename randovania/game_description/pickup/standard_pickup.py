import dataclasses
from dataclasses import dataclass
from typing import Self

from frozendict import frozendict

from randovania.game_description.pickup.pickup_category import PickupCategory
from randovania.game_description.resources.location_category import LocationCategory
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.game import RandovaniaGame
from randovania.lib import frozen_lib


@dataclass(frozen=True)
class StandardPickupDefinition:
    game: RandovaniaGame
    name: str
    pickup_category: PickupCategory
    broad_category: PickupCategory
    model_name: str
    progression: tuple[str, ...]
    default_shuffled_count: int
    default_starting_count: int
    preferred_location_category: LocationCategory
    ammo: tuple[str, ...] = tuple()
    unlocks_ammo: bool = False
    additional_resources: frozendict[str, int] = dataclasses.field(default_factory=frozendict)
    hide_from_gui: bool = False
    must_be_starting: bool = False
    original_location: PickupIndex | None = None
    probability_offset: int = 0
    probability_multiplier: float = 1
    description: str | None = None
    extra: frozendict = dataclasses.field(default_factory=frozendict)

    def __post_init__(self):
        if not self.progression and not self.ammo:
            raise ValueError(f"Item {self.name} has no progression nor ammo.")

    @classmethod
    def from_json(cls, name: str, value: dict, game: RandovaniaGame,
                  pickup_categories: dict[str, PickupCategory]) -> Self:
        return cls(
            game=game,
            name=name,
            pickup_category=pickup_categories[value["pickup_category"]],
            broad_category=pickup_categories[value["broad_category"]],
            model_name=value["model_name"],
            progression=frozen_lib.wrap(value["progression"]),
            default_shuffled_count=value["default_shuffled_count"],
            default_starting_count=value["default_starting_count"],
            ammo=frozen_lib.wrap(value.get("ammo", [])),
            unlocks_ammo=value.get("unlocks_ammo", False),
            additional_resources=frozen_lib.wrap(value.get("additional_resources", {})),
            hide_from_gui=value.get("hide_from_gui", False),
            must_be_starting=value.get("must_be_starting", False),
            original_location=PickupIndex(value["original_location"]) if "original_location" in value else None,
            probability_offset=value["probability_offset"],
            probability_multiplier=value["probability_multiplier"],
            description=value.get("description"),
            preferred_location_category=LocationCategory(value["preferred_location_category"]),
            extra=frozen_lib.wrap(value.get("extra", {})),
        )

    @property
    def as_json(self) -> dict:
        result = {
            "pickup_category": self.pickup_category.name,
            "broad_category": self.broad_category.name,
            "model_name": self.model_name,
            "progression": frozen_lib.unwrap(self.progression),
            "default_shuffled_count": self.default_shuffled_count,
            "default_starting_count": self.default_starting_count,
            "ammo": frozen_lib.unwrap(self.ammo),
            "unlocks_ammo": self.unlocks_ammo,
            "additional_resources": frozen_lib.unwrap(self.additional_resources),
            "hide_from_gui": self.hide_from_gui,
            "must_be_starting": self.must_be_starting,
            "probability_offset": self.probability_offset,
            "probability_multiplier": self.probability_multiplier,
            "preferred_location_category": self.preferred_location_category.value,
            "extra": frozen_lib.unwrap(self.extra),
        }
        if self.original_location is not None:
            result["original_location"] = self.original_location.index
        if self.description is not None:
            result["description"] = self.description
        return result
