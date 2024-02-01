import dataclasses
from random import Random

from randovania.game_description.game_description import GameDescription
from randovania.layout.base.base_configuration import BaseConfiguration


@dataclasses.dataclass(frozen=True)
class PreFillParams:
    rng: Random
    configuration: BaseConfiguration
    game: GameDescription
    is_multiworld: bool
