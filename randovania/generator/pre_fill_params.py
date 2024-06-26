import dataclasses
from random import Random

from randovania.game_description.game_database_view import GameDatabaseView
from randovania.layout.base.base_configuration import BaseConfiguration


@dataclasses.dataclass(frozen=True)
class PreFillParams:
    rng: Random
    configuration: BaseConfiguration
    game: GameDatabaseView
    is_multiworld: bool
