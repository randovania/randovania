from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import Self

from frozendict import frozendict

from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.bitpacking.type_enforcement import DataclassPostInitTypeCheck
from randovania.game_description.pickup.pickup_category import PickupCategory
from randovania.game_description.resources.location_category import LocationCategory
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.game import RandovaniaGame
from randovania.layout.base.standard_pickup_state import StandardPickupStateCase

EXCLUDE_DEFAULT = {"exclude_if_default": True}


@dataclass(frozen=True)
class StandardPickupDefinition(JsonDataclass, DataclassPostInitTypeCheck):
    game: RandovaniaGame = dataclasses.field(metadata={"init_from_extra": True})
    name: str = dataclasses.field(metadata={"init_from_extra": True})
    pickup_category: PickupCategory = dataclasses.field(metadata={"init_from_extra": True})
    broad_category: PickupCategory = dataclasses.field(metadata={"init_from_extra": True})
    model_name: str
    offworld_models: frozendict[RandovaniaGame, str]
    progression: tuple[str, ...]
    preferred_location_category: LocationCategory
    expected_case_for_describer: StandardPickupStateCase = dataclasses.field(default=StandardPickupStateCase.SHUFFLED)
    custom_count_for_shuffled_case: int | None = dataclasses.field(default=None, metadata=EXCLUDE_DEFAULT)
    custom_count_for_starting_case: int | None = dataclasses.field(default=None, metadata=EXCLUDE_DEFAULT)
    ammo: tuple[str, ...] = dataclasses.field(default_factory=tuple, metadata=EXCLUDE_DEFAULT)
    unlocks_ammo: bool = dataclasses.field(default=False, metadata=EXCLUDE_DEFAULT)
    additional_resources: frozendict[str, int] = dataclasses.field(default_factory=frozendict, metadata=EXCLUDE_DEFAULT)
    hide_from_gui: bool = dataclasses.field(default=False, metadata=EXCLUDE_DEFAULT)
    must_be_starting: bool = dataclasses.field(default=False, metadata=EXCLUDE_DEFAULT)
    original_locations: tuple[PickupIndex, ...] = dataclasses.field(default_factory=tuple, metadata=EXCLUDE_DEFAULT)
    probability_offset: float = dataclasses.field(default=0.0, metadata=EXCLUDE_DEFAULT)
    probability_multiplier: float = dataclasses.field(default=1.0, metadata=EXCLUDE_DEFAULT)
    description: str | None = dataclasses.field(default=None, metadata=EXCLUDE_DEFAULT)
    extra: frozendict = dataclasses.field(default_factory=frozendict, metadata=EXCLUDE_DEFAULT)

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.progression and not self.ammo:
            raise ValueError(f"Standard Pickup {self.name} has no progression nor ammo.")

        if self.count_for_shuffled_case < 1:
            raise ValueError(f"Standard Pickup {self.name} count for shuffled case is less than 1.")

        if self.count_for_starting_case < 1:
            raise ValueError(f"Standard Pickup {self.name} count for starting case is less than 1.")

    @classmethod
    def from_json_with_categories(
        cls, name: str, game: RandovaniaGame, pickup_categories: dict[str, PickupCategory], value: dict
    ) -> Self:
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

    @property
    def count_for_shuffled_case(self) -> int:
        """How many pickups StandardPickupStateCase.SHUFFLED includes. Defaults to length of progression.
        Can be manually set via custom_count_for_shuffled_case. Must be at least 1."""
        if self.custom_count_for_shuffled_case is None:
            return len(self.progression)
        return self.custom_count_for_shuffled_case

    @property
    def count_for_starting_case(self) -> int:
        """How many pickups StandardPickupStateCase.STARTING_ITEM includes. Defaults to 1.
        Can be manually set via custom_count_for_starting_case. Must be at least 1."""
        if self.custom_count_for_starting_case is None:
            return 1
        return self.custom_count_for_starting_case
