from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from randovania.bitpacking.bitpacking import BitPackEnum
from randovania.games.prime_origins.layout.prime_origins_configuration import MPOConfiguration

if TYPE_CHECKING:
    from randovania.game_description.game_database_view import GameDatabaseView
    from randovania.generator.pickup_pool import PoolResults
    from randovania.layout.base.base_configuration import BaseConfiguration


class InGameMode(BitPackEnum, Enum):
    CLASSIC = "Classic"
    REMIX = "Remix"


def pool_creator(results: PoolResults, configuration: BaseConfiguration, game: GameDatabaseView) -> None:
    assert isinstance(configuration, MPOConfiguration)
