from __future__ import annotations

import dataclasses

from randovania.bitpacking.json_dataclass import EXCLUDE_DEFAULT
from randovania.game_description.pickup.pickup_definition.base_pickup import (
    BasePickupDefinition,
)
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.layout.base.standard_pickup_state import StandardPickupStateCase


@dataclasses.dataclass(frozen=True, kw_only=True)
class StandardPickupDefinition(BasePickupDefinition):
    """Encodes a StandardPickup in the pickup_database json"""

    progression: tuple[str, ...]
    """
    Defines item resources (as short names) that collecting this pickup provides.
    If this tuple contains only one resource, then every collection will give that resource.
    If it contains more than one, then every time the pickup will be collected, it will give the Nth resource.
    """

    ammo: tuple[str, ...] = dataclasses.field(default_factory=tuple, metadata=EXCLUDE_DEFAULT)
    """
    Defines item resources (as short names) which all will be provided when the pickup is collected.
    A user is able to customize how much of each ammo is given upon collection.
    """

    unlocks_ammo: bool = dataclasses.field(default=False, metadata=EXCLUDE_DEFAULT)
    """Determines whether collecting the pickup allows to immediately use all ammo defined in the 'ammo' field."""

    show_in_credits_spoiler: bool = dataclasses.field(default=True, metadata=EXCLUDE_DEFAULT)
    """
    Whether the pickup should be displayed in the standard credits spoiler used by many games.
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

    hide_from_gui: bool = dataclasses.field(default=False, metadata=EXCLUDE_DEFAULT)
    """Whether this pickup should be hidden in the GUI."""

    must_be_starting: bool = dataclasses.field(default=False, metadata=EXCLUDE_DEFAULT)
    """Whether the pickup is required be a starting item."""

    original_locations: tuple[PickupIndex, ...] = dataclasses.field(default_factory=tuple, metadata=EXCLUDE_DEFAULT)
    """
    The indices of the pickup locations (defined in the database) on where the pickup(s) should be located if
    it's set to be at the original location.
    """

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.progression and not self.ammo:
            raise ValueError(f"Standard Pickup {self.name} has no progression nor ammo.")

        if self.count_for_shuffled_case < 1:
            raise ValueError(f"Standard Pickup {self.name} count for shuffled case is less than 1.")

        if self.count_for_starting_case < 1:
            raise ValueError(f"Standard Pickup {self.name} count for starting case is less than 1.")

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

    @property
    def json_field_order(self) -> list[str]:
        return [
            "gui_category",
            "hint_features",
            "model_name",
            "offworld_models",
            "preferred_location_category",
            "progression",
            "additional_resources",
            "ammo",
            "unlocks_ammo",
            "show_in_credits_spoiler",
            "expected_case_for_describer",
            "custom_count_for_shuffled_case",
            "custom_count_for_starting_case",
            "hide_from_gui",
            "must_be_starting",
            "original_locations",
            "index_age_impact",
            "probability_offset",
            "probability_multiplier",
            "description",
            "extra",
        ]
