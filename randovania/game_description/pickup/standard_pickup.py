from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import Self

from frozendict import frozendict

from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.bitpacking.type_enforcement import DataclassPostInitTypeCheck
from randovania.game.game_enum import RandovaniaGame
from randovania.game_description.pickup.pickup_category import PickupCategory
from randovania.game_description.resources.location_category import LocationCategory
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.layout.base.standard_pickup_state import StandardPickupStateCase

EXCLUDE_DEFAULT = {"exclude_if_default": True}


@dataclass(frozen=True)
class StandardPickupDefinition(JsonDataclass, DataclassPostInitTypeCheck):
    game: RandovaniaGame = dataclasses.field(metadata={"init_from_extra": True})
    """The game this pickup comes from."""

    name: str = dataclasses.field(metadata={"init_from_extra": True})
    """The name of the pickup."""

    pickup_category: PickupCategory = dataclasses.field(metadata={"init_from_extra": True})
    """
    The precise category for this pickup. Used in the GUI for visually grouping pickups with the same precise
    category, and for when this pickup is referenced by a precise hint.
    """

    broad_category: PickupCategory = dataclasses.field(metadata={"init_from_extra": True})
    """The broad category for this pickup. Used for when this pickup is referenced by a broad hint."""

    model_name: str
    """The name of the model that should be used by default for this pickup."""

    offworld_models: frozendict[RandovaniaGame, str]
    """A dictionary defining the name of the model for other games if this pickup is in their world."""

    progression: tuple[str, ...]
    """
    Defines item resources (as short names) that collecting this pickup provides.
    If this tuple contains only one resource, then every collection will give that resource.
    If it contains more than one, then every time the pickup will be collected, it will give the Nth resource.
    """

    preferred_location_category: LocationCategory
    """
    The category for the preferred location. Used to determine where to place this Pickup when Major/Minor placement
    is enabled, and for when this pickup is referenced by a major/minor hint.
    """

    expected_case_for_describer: StandardPickupStateCase = dataclasses.field(default=StandardPickupStateCase.SHUFFLED)
    """What the expected case for the Preset Describer should be."""

    custom_count_for_shuffled_case: int | None = dataclasses.field(default=None, metadata=EXCLUDE_DEFAULT)
    """
    Defines how often the pickup is shuffled, if the pickup is set to StandardPickupStateCase.SHUFFLED.
    If not specified, will use the length of progression.
    """

    custom_count_for_starting_case: int | None = dataclasses.field(default=None, metadata=EXCLUDE_DEFAULT)
    """
    Defines with how many pickups will be given as a starting item, if the pickup is set to
    StandardPickupStateCase.STARTING_ITEM. If not specified, will use the length of progression.
    """

    ammo: tuple[str, ...] = dataclasses.field(default_factory=tuple, metadata=EXCLUDE_DEFAULT)
    """
    Defines item resources (as short names) which all will be provided when the pickup is collected.
    A user is able to customize how much of each ammo is given upon collection.
    """

    unlocks_ammo: bool = dataclasses.field(default=False, metadata=EXCLUDE_DEFAULT)
    """Determines whether collecting the pickup allows to immediately use all ammo defined in the 'ammo' field."""

    additional_resources: frozendict[str, int] = dataclasses.field(default_factory=frozendict, metadata=EXCLUDE_DEFAULT)
    """Defines item resources (as short names) which all will be additionally provided when the pickup is collected."""

    hide_from_gui: bool = dataclasses.field(default=False, metadata=EXCLUDE_DEFAULT)
    """Whether this pickup should be hidden in the GUI."""

    must_be_starting: bool = dataclasses.field(default=False, metadata=EXCLUDE_DEFAULT)
    """Whether the pickup is required be a starting item."""

    original_locations: tuple[PickupIndex, ...] = dataclasses.field(default_factory=tuple, metadata=EXCLUDE_DEFAULT)
    """
    The indices of the pickup locations (defined in the database) on where the pickup(s) should be located if
    it's set to be at the original location.
    """

    probability_offset: float = dataclasses.field(default=0.0, metadata=EXCLUDE_DEFAULT)
    """During generation, determines how much the weight when placing the pickup will be offset."""

    probability_multiplier: float = dataclasses.field(default=1.0, metadata=EXCLUDE_DEFAULT)
    """During generation, determines by how much the weight when placing the pickup will be multiplied."""

    description: str | None = dataclasses.field(default=None, metadata=EXCLUDE_DEFAULT)
    """An extra description of the pickup. Will be used in the GUI for more info."""

    extra: frozendict = dataclasses.field(default_factory=frozendict, metadata=EXCLUDE_DEFAULT)
    """
    A dictionary that can contain any arbitrary game-specific extra information.
    Developers can use the game-specific however they need to.
    """

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
