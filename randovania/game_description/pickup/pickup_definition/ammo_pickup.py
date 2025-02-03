from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import TYPE_CHECKING

from randovania.bitpacking.json_dataclass import EXCLUDE_DEFAULT
from randovania.game_description.pickup.pickup_definition.base_pickup import (
    BasePickupDefinition,
)
from randovania.game_description.pickup.pickup_entry import ResourceLock

if TYPE_CHECKING:
    from randovania.game_description.resources.resource_database import ResourceDatabase


@dataclass(frozen=True, kw_only=True, order=True)
class AmmoPickupDefinition(BasePickupDefinition):
    """Encodes an AmmoPickup in the pickup_database json"""

    items: tuple[str, ...]
    """
    Defines item resources (as short names) which all will be provided when the pickup is collected.
    A user is able to customize how much of each ammo is given upon collection.
    """

    unlocked_by: str | None = dataclasses.field(default=None, metadata=EXCLUDE_DEFAULT)
    """
    Defines which item resource (as short name) unlocks the ammo provided by this pickup.
    If unset, the ammo is always provided.
    """

    temporary: str | None = dataclasses.field(default=None, metadata=EXCLUDE_DEFAULT)
    """
    Defines which item resource (as short name) keeps track of ammo collected from this pickup
    before the real ammo has been unlocked.
    Must be set when `unlocked_by` is set.
    """

    allows_negative: bool = dataclasses.field(default=False, metadata=EXCLUDE_DEFAULT)
    """Determines whether the user can configure this expansion to remove maximum ammo rather than provide it."""

    include_expected_counts: bool = dataclasses.field(default=True, metadata=EXCLUDE_DEFAULT)
    """Whether to indicate the maximum ammo from this source in the item pool tab."""
    explain_other_sources: bool = dataclasses.field(default=True, metadata=EXCLUDE_DEFAULT)
    """Whether to indicate the maximum ammo from other sources in the item pool tab."""
    mention_limit: bool = dataclasses.field(default=True, metadata=EXCLUDE_DEFAULT)
    """Whether to indicate the overall maximum ammo in the item pool tab."""

    # override defaults from parent
    probability_multiplier: float = dataclasses.field(default=2.0, metadata=EXCLUDE_DEFAULT)
    """During generation, determines by how much the weight when placing the pickup will be multiplied."""

    # TODO: change later to lower number after more experimentation and adjust in test_pickup_creator
    index_age_impact: float = dataclasses.field(default=1.0, metadata=EXCLUDE_DEFAULT)
    """
    During generation, determines by how much to increase all reachable location's age before this pickup is placed.
    The older a location is, the less likely it is for future pickups to be placed there.
    """

    def __post_init__(self) -> None:
        if self.temporary is not None:
            if self.unlocked_by is None:
                raise ValueError("If temporary is set, unlocked_by must be set.")
            if len(self.items) != 1:
                raise ValueError(f"If temporary is set, only one item is supported. Got {len(self.items)} instead")
        elif self.unlocked_by is not None:
            raise ValueError("If temporary is not set, unlocked_by must not be set.")

    def create_resource_lock(self, resource_database: ResourceDatabase) -> ResourceLock | None:
        if self.unlocked_by is not None:
            assert self.temporary is not None
            return ResourceLock(
                locked_by=resource_database.get_item(self.unlocked_by),
                item_to_lock=resource_database.get_item(self.items[0]),
                temporary_item=resource_database.get_item(self.temporary),
            )
        return None

    @property
    def json_field_order(self) -> list[str]:
        return [
            "gui_category",
            "hint_features",
            "model_name",
            "offworld_models",
            "preferred_location_category",
            "items",
            "additional_resources",
            "unlocked_by",
            "temporary",
            "allows_negative",
            "include_expected_counts",
            "explain_other_sources",
            "mention_limit",
            "index_age_impact",
            "probability_offset",
            "probability_multiplier",
            "description",
            "extra",
        ]
