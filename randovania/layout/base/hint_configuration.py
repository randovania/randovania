import dataclasses
import typing
from collections.abc import Iterator
from enum import Enum
from typing import Self, override

from frozendict import frozendict

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDataclass, BitPackDecoder, BitPackEnum
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
    """When false, all random hints are replaced with jokes."""

    enable_specific_location_hints: bool
    """When false, all specific location hints are replaced with jokes."""

    specific_pickup_hints: frozendict[str, SpecificPickupHintMode] = dataclasses.field(
        metadata={"manual_bitpacking": True}
    )
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

    def settings_incompatible_with_multiworld(self) -> list[str]:
        incompatible = []
        if self.use_resolver_hints:
            incompatible.append("Resolver-based hints")
        return incompatible

    @override
    def bit_pack_encode(self, metadata: dict) -> Iterator[tuple[int, int]]:
        reference = typing.cast("HintConfiguration", metadata["reference"])

        modified_specific_hints = [
            hint
            for hint, mode in sorted(reference.specific_pickup_hints.items())
            if self.specific_pickup_hints[hint] != mode
        ]
        yield from bitpacking.pack_sorted_array_elements(
            modified_specific_hints,
            sorted(reference.specific_pickup_hints.keys()),
        )
        for hint in modified_specific_hints:
            yield from self.specific_pickup_hints[hint].bit_pack_encode(
                {"reference": reference.specific_pickup_hints[hint]}
            )

        yield from super().bit_pack_encode(metadata)

    @override
    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder, metadata: dict) -> Self:
        reference = typing.cast("HintConfiguration", metadata["reference"])

        modified_specific_hints = bitpacking.decode_sorted_array_elements(
            decoder, sorted(reference.specific_pickup_hints.keys())
        )
        specific_hints = dict(reference.specific_pickup_hints)
        for hint in modified_specific_hints:
            specific_hints[hint] = SpecificPickupHintMode.bit_pack_unpack(
                decoder, {"reference": reference.specific_pickup_hints[hint]}
            )

        meta = dict(metadata)
        meta.setdefault("extra_args", {})
        meta["extra_args"]["specific_pickup_hints"] = frozendict(specific_hints)

        return super().bit_pack_unpack(decoder, meta)
