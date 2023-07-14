from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from open_prime_rando.dol_patching.echoes.beam_configuration import BeamAmmoConfiguration

from randovania.bitpacking.bitpacking import BitPackDataclass
from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.bitpacking.type_enforcement import DataclassPostInitTypeCheck

if TYPE_CHECKING:
    from collections.abc import Iterator


@dataclasses.dataclass(frozen=True)
class RdvBeamAmmoConfiguration(BeamAmmoConfiguration, BitPackDataclass, JsonDataclass, DataclassPostInitTypeCheck):
    pass


@dataclasses.dataclass(frozen=True)
class BeamConfiguration(BitPackDataclass, JsonDataclass):
    power: RdvBeamAmmoConfiguration
    dark: RdvBeamAmmoConfiguration
    light: RdvBeamAmmoConfiguration
    annihilator: RdvBeamAmmoConfiguration

    @property
    def all_beams(self) -> Iterator[RdvBeamAmmoConfiguration]:
        yield self.power
        yield self.dark
        yield self.light
        yield self.annihilator
