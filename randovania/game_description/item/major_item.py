import dataclasses
from dataclasses import dataclass

from frozendict import frozendict

from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.game import RandovaniaGame
from randovania.lib import frozen_lib


@dataclass(frozen=True)
class MajorItem:
    game: RandovaniaGame
    name: str
    item_category: ItemCategory
    broad_category: ItemCategory
    model_name: str
    progression: tuple[str, ...]
    default_shuffled_count: int
    default_starting_count: int
    ammo_index: tuple[str, ...] = tuple()
    unlocks_ammo: bool = False
    hide_from_gui: bool = False
    must_be_starting: bool = False
    original_index: PickupIndex | None = None
    probability_offset: int = 0
    probability_multiplier: float = 1
    warning: str | None = None
    extra: frozendict = dataclasses.field(default_factory=frozendict)

    def __post_init__(self):
        if not self.progression and not self.ammo_index:
            raise ValueError(f"Item {self.name} has no progression nor ammo.")

    @classmethod
    def from_json(cls, name: str, value: dict, game: RandovaniaGame,
                  item_categories: dict[str, ItemCategory]) -> "MajorItem":
        return cls(
            game=game,
            name=name,
            item_category=item_categories[value["item_category"]],
            broad_category=item_categories[value["broad_category"]],
            model_name=value["model_name"],
            progression=frozen_lib.wrap(value["progression"]),
            default_shuffled_count=value["default_shuffled_count"],
            default_starting_count=value["default_starting_count"],
            ammo_index=frozen_lib.wrap(value.get("ammo", [])),
            unlocks_ammo=value.get("unlocks_ammo", False),
            hide_from_gui=value.get("hide_from_gui", False),
            must_be_starting=value.get("must_be_starting", False),
            original_index=PickupIndex(value["original_index"]) if "original_index" in value else None,
            probability_offset=value["probability_offset"],
            probability_multiplier=value["probability_multiplier"],
            warning=value.get("warning"),
            extra=frozen_lib.wrap(value.get("extra", {}))
        )

    @property
    def as_json(self) -> dict:
        result = {
            "item_category": self.item_category.name,
            "broad_category": self.broad_category.name,
            "model_name": self.model_name,
            "progression": frozen_lib.unwrap(self.progression),
            "default_shuffled_count": self.default_shuffled_count,
            "default_starting_count": self.default_starting_count,
            "ammo": frozen_lib.unwrap(self.ammo_index),
            "unlocks_ammo": self.unlocks_ammo,
            "hide_from_gui": self.hide_from_gui,
            "must_be_starting": self.must_be_starting,
            "probability_offset": self.probability_offset,
            "probability_multiplier": self.probability_multiplier,
            "extra": frozen_lib.unwrap(self.extra),
        }
        if self.original_index is not None:
            result["original_index"] = self.original_index.index
        if self.warning is not None:
            result["warning"] = self.warning
        return result
