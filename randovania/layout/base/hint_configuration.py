import dataclasses
from enum import Enum

from frozendict import frozendict

from randovania.bitpacking.bitpacking import BitPackDataclass, BitPackEnum
from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.bitpacking.type_enforcement import DataclassPostInitTypeCheck
from randovania.lib import enum_lib


class SpecificPickupHintMode(BitPackEnum, Enum):
    DISABLED = "disabled"
    HIDE_AREA = "hide-area"
    PRECISE = "precise"

    long_name: str
    description: str


enum_lib.add_long_name(
    SpecificPickupHintMode,
    {
        SpecificPickupHintMode.DISABLED: "Disabled",
        SpecificPickupHintMode.HIDE_AREA: "Region only",
        SpecificPickupHintMode.PRECISE: "Region and area",
    },
)

enum_lib.add_per_enum_field(
    SpecificPickupHintMode,
    "description",
    {
        SpecificPickupHintMode.DISABLED: "No hint",
        SpecificPickupHintMode.HIDE_AREA: "Show only the region name",
        SpecificPickupHintMode.PRECISE: "Show region and area name",
    },
)


@dataclasses.dataclass(frozen=True)
class HintConfiguration(BitPackDataclass, JsonDataclass, DataclassPostInitTypeCheck):
    # basic settings
    enable_random_hints: bool
    """When false, all hints are replaced with jokes."""

    specific_pickup_hints: frozendict[str, SpecificPickupHintMode]
    """What level of precision to use for a given specific pickup hint (e.g. Artifacts)"""

    # experimental settings / hidden from GUI
    minimum_available_locations_for_hint_placement: int = dataclasses.field(metadata={"min": 0, "max": 99})
    minimum_location_weight_for_hint_placement: float = dataclasses.field(
        metadata={
            "min": 0.0,
            "max": 5.0,
            "precision": 0.1,
        }
    )
    use_resolver_hints: bool
