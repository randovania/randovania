import dataclasses
from typing import Optional, Tuple

from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo


@dataclasses.dataclass(frozen=True)
class EchoesBeamConfiguration:
    item: ItemResourceInfo
    ammo_a: Optional[ItemResourceInfo]
    ammo_b: Optional[ItemResourceInfo]
    uncharged_cost: int
    charged_cost: int
    combo_missile_cost: int
    combo_ammo_cost: int


@dataclasses.dataclass(frozen=True)
class EchoesGameSpecific:
    energy_per_tank: float
    safe_zone_heal_per_second: float
    beam_configurations: Tuple[EchoesBeamConfiguration, ...]
    dangerous_energy_tank: bool
