from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.yokus_island_express.layout.yokus_island_express_configuration import YokuConfiguration

if TYPE_CHECKING:
    from randovania.game_description.game_database_view import GameDatabaseView
    from randovania.generator.pickup_pool import PoolResults
    from randovania.layout.base.base_configuration import BaseConfiguration


def pool_creator(results: PoolResults, configuration: BaseConfiguration, game: GameDatabaseView) -> None:
    assert isinstance(configuration, YokuConfiguration)
