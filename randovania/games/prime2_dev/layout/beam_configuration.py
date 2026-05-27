from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from randovania.bitpacking.bitpacking import BitPackDataclass
from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.bitpacking.type_enforcement import DataclassPostInitTypeCheck

if TYPE_CHECKING:
    from collections.abc import Iterator


@dataclasses.dataclass(frozen=True)
class BeamAmmoConfiguration(BitPackDataclass, JsonDataclass, DataclassPostInitTypeCheck):
    item_index: int = dataclasses.field(metadata={"min": 0, "max": 108})
    ammo_a: int = dataclasses.field(metadata={"min": -1, "max": 108})
    ammo_b: int = dataclasses.field(metadata={"min": -1, "max": 108})
    uncharged_cost: int = dataclasses.field(metadata={"min": 0, "max": 250, "if_different": 1})
    charged_cost: int = dataclasses.field(metadata={"min": 0, "max": 250, "if_different": 5})
    combo_missile_cost: int = dataclasses.field(metadata={"min": 1, "max": 250, "if_different": 5})
    combo_ammo_cost: int = dataclasses.field(metadata={"min": 0, "max": 250, "if_different": 30})


@dataclasses.dataclass(frozen=True)
class BeamConfiguration(BitPackDataclass, JsonDataclass):
    power: BeamAmmoConfiguration
    dark: BeamAmmoConfiguration
    light: BeamAmmoConfiguration
    annihilator: BeamAmmoConfiguration

    @property
    def all_beams(self) -> Iterator[BeamAmmoConfiguration]:
        yield self.power
        yield self.dark
        yield self.light
        yield self.annihilator
