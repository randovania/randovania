import dataclasses
from dataclasses import dataclass
from typing import Self

from frozendict import frozendict

from randovania.game_description.pickup.pickup_category import PickupCategory
from randovania.game_description.resources.location_category import LocationCategory
from randovania.game_description.resources.pickup_entry import ResourceLock
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.games.game import RandovaniaGame
from randovania.lib import frozen_lib


@dataclass(frozen=True, order=True)
class AmmoPickupDefinition:
    game: RandovaniaGame
    name: str
    model_name: str
    items: tuple[str, ...]
    preferred_location_category: LocationCategory
    broad_category: PickupCategory
    additional_resources: frozendict[str, int] = dataclasses.field(default_factory=frozendict)
    unlocked_by: str | None = None
    temporary: str | None = None
    allows_negative: bool | None = None
    description: str | None = None
    extra: frozendict = dataclasses.field(default_factory=frozendict)

    def __post_init__(self):
        if self.temporary is not None:
            if self.unlocked_by is None:
                raise ValueError("If temporaries is set, unlocked_by must be set.")
            if len(self.items) != 1:
                raise ValueError("If temporaries is set, only one item is supported. Got {} instead".format(
                    len(self.items)
                ))
        elif self.unlocked_by is not None:
            raise ValueError("If temporaries is not set, unlocked_by must not be set.")

    @classmethod
    def from_json(cls, name: str, value: dict, game: RandovaniaGame,
                  pickup_categories: dict[str, PickupCategory]) -> Self:
        return cls(
            game=game,
            name=name,
            model_name=value["model_name"],
            items=frozen_lib.wrap(value["items"]),
            preferred_location_category=LocationCategory(value["preferred_location_category"]),
            broad_category=pickup_categories[value["broad_category"]],
            additional_resources=frozen_lib.wrap(value.get("additional_resources", {})),
            unlocked_by=value.get("unlocked_by"),
            temporary=value.get("temporary"),
            allows_negative=value.get("allows_negative"),
            description=value.get("description"),
            extra=frozen_lib.wrap(value.get("extra", {}))
        )

    @property
    def as_json(self) -> dict:
        result = {
            "model_name": self.model_name,
            "items": frozen_lib.unwrap(self.items),
            "preferred_location_category": self.preferred_location_category.value,
            "broad_category": self.broad_category.name,
            "additional_resources": frozen_lib.unwrap(self.additional_resources),
            "extra": frozen_lib.unwrap(self.extra),
        }
        if self.unlocked_by is not None:
            result["temporary"] = self.temporary
            result["unlocked_by"] = self.unlocked_by
        if self.allows_negative is not None:
            result["allows_negative"] = self.allows_negative
        if self.description is not None:
            result["description"] = self.description
        return result

    @property
    def pickup_category(self) -> PickupCategory:
        return AMMO_PICKUP_CATEGORY

    def create_resource_lock(self, resource_database: ResourceDatabase) -> ResourceLock | None:
        if self.unlocked_by is not None:
            return ResourceLock(
                locked_by=resource_database.get_item(self.unlocked_by),
                item_to_lock=resource_database.get_item(self.items[0]),
                temporary_item=resource_database.get_item(self.temporary),
            )
        return None


AMMO_PICKUP_CATEGORY = PickupCategory(
    name="expansion",
    long_name="Expansion",
    hint_details=("an ", "expansion"),
    hinted_as_major=False
)
