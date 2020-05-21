import dataclasses
from typing import Optional, Tuple

from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo


@dataclasses.dataclass(frozen=True)
class EchoesBeamConfiguration:
    item: SimpleResourceInfo
    ammo_a: Optional[SimpleResourceInfo]
    ammo_b: Optional[SimpleResourceInfo]
    uncharged_cost: int
    charged_cost: int
    combo_missile_cost: int
    combo_ammo_cost: int


@dataclasses.dataclass(frozen=True)
class EchoesGameSpecific:
    energy_per_tank: float
    beam_configurations: Tuple[EchoesBeamConfiguration, ...]