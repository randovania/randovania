import dataclasses
from dataclasses import dataclass

from frozendict import frozendict

from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.resources.location_category import LocationCategory
from randovania.game_description.resources.pickup_entry import ResourceLock
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.games.game import RandovaniaGame
from randovania.lib import frozen_lib


@dataclass(frozen=True, order=True)
class Ammo:
    game: RandovaniaGame
    name: str
    model_name: str
    items: tuple[str, ...]
    preferred_location_category: LocationCategory
    broad_category: ItemCategory
    unlocked_by: str | None = None
    temporary: str | None = None
    is_major: bool | None = None
    allows_negative: bool | None = None
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
                  item_categories: dict[str, ItemCategory]) -> "Ammo":
        return cls(
            game=game,
            name=name,
            model_name=value["model_name"],
            items=frozen_lib.wrap(value["items"]),
            preferred_location_category=LocationCategory(value["preferred_location_category"]),
            broad_category=item_categories[value["broad_category"]],
            unlocked_by=value.get("unlocked_by"),
            temporary=value.get("temporary"),
            is_major=value.get("is_major"),
            allows_negative=value.get("allows_negative"),
            extra=frozen_lib.wrap(value.get("extra", {}))
        )

    @property
    def as_json(self) -> dict:
        result = {
            "model_name": self.model_name,
            "items": frozen_lib.unwrap(self.items),
            "preferred_location_category": self.preferred_location_category.value,
            "broad_category": self.broad_category.name,
            "extra": frozen_lib.unwrap(self.extra),
        }
        if self.unlocked_by is not None:
            result["temporary"] = self.temporary
            result["unlocked_by"] = self.unlocked_by
        if self.is_major is not None:
            result["is_major"] = self.is_major
        if self.allows_negative is not None:
            result["allows_negative"] = self.allows_negative
        return result

    @property
    def item_category(self) -> ItemCategory:
        return AMMO_ITEM_CATEGORY

    def create_resource_lock(self, resource_database: ResourceDatabase) -> ResourceLock | None:
        if self.unlocked_by is not None:
            return ResourceLock(
                locked_by=resource_database.get_item(self.unlocked_by),
                item_to_lock=resource_database.get_item(self.items[0]),
                temporary_item=resource_database.get_item(self.temporary),
            )
        return None


AMMO_ITEM_CATEGORY = ItemCategory(
    name="expansion",
    long_name="Expansion",
    hint_details=("an ", "expansion"),
    is_major=False
)
