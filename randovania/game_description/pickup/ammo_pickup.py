from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import TYPE_CHECKING, Self

from frozendict import frozendict

from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.game_description.pickup.pickup_category import PickupCategory
from randovania.game_description.pickup.pickup_entry import ResourceLock
from randovania.game_description.resources.location_category import LocationCategory
from randovania.games.game import RandovaniaGame

if TYPE_CHECKING:
    from randovania.game_description.resources.resource_database import ResourceDatabase

EXCLUDE_DEFAULT = {"exclude_if_default": True}


@dataclass(frozen=True, order=True)
class AmmoPickupDefinition(JsonDataclass):
    game: RandovaniaGame = dataclasses.field(metadata={"init_from_extra": True})
    name: str = dataclasses.field(metadata={"init_from_extra": True})
    model_name: str
    offworld_models: frozendict[RandovaniaGame, str]
    items: tuple[str, ...]
    preferred_location_category: LocationCategory
    broad_category: PickupCategory = dataclasses.field(metadata={"init_from_extra": True})
    additional_resources: frozendict[str, int] = dataclasses.field(default_factory=frozendict, metadata=EXCLUDE_DEFAULT)
    unlocked_by: str | None = dataclasses.field(default=None, metadata=EXCLUDE_DEFAULT)
    temporary: str | None = dataclasses.field(default=None, metadata=EXCLUDE_DEFAULT)
    allows_negative: bool | None = dataclasses.field(default=None, metadata=EXCLUDE_DEFAULT)
    description: str | None = dataclasses.field(default=None, metadata=EXCLUDE_DEFAULT)
    include_expected_counts: bool = dataclasses.field(default=True, metadata=EXCLUDE_DEFAULT)
    explain_other_sources: bool = dataclasses.field(default=True, metadata=EXCLUDE_DEFAULT)
    mention_limit: bool = dataclasses.field(default=True, metadata=EXCLUDE_DEFAULT)
    extra: frozendict = dataclasses.field(default_factory=frozendict, metadata=EXCLUDE_DEFAULT)

    def __post_init__(self) -> None:
        if self.temporary is not None:
            if self.unlocked_by is None:
                raise ValueError("If temporaries is set, unlocked_by must be set.")
            if len(self.items) != 1:
                raise ValueError(f"If temporaries is set, only one item is supported. Got {len(self.items)} instead")
        elif self.unlocked_by is not None:
            raise ValueError("If temporaries is not set, unlocked_by must not be set.")

    @classmethod
    def from_json_with_categories(
        cls, name: str, game: RandovaniaGame, pickup_categories: dict[str, PickupCategory], value: dict
    ) -> Self:
        return cls.from_json(
            value,
            game=game,
            name=name,
            broad_category=pickup_categories[value["broad_category"]],
        )

    @property
    def as_json(self) -> dict:
        return {
            "broad_category": self.broad_category.name,
            **super().as_json,
        }

    @property
    def pickup_category(self) -> PickupCategory:
        return AMMO_PICKUP_CATEGORY

    def create_resource_lock(self, resource_database: ResourceDatabase) -> ResourceLock | None:
        if self.unlocked_by is not None:
            assert self.temporary is not None
            return ResourceLock(
                locked_by=resource_database.get_item(self.unlocked_by),
                item_to_lock=resource_database.get_item(self.items[0]),
                temporary_item=resource_database.get_item(self.temporary),
            )
        return None


AMMO_PICKUP_CATEGORY = PickupCategory(
    name="expansion", long_name="Expansion", hint_details=("an ", "expansion"), hinted_as_major=False
)
