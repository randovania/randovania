from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.blank.layout.blank_configuration import BlankConfiguration
from randovania.generator.pickup_pool.pickup_creator import create_generated_pickup

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.generator.pickup_pool import PoolResults
    from randovania.layout.base.base_configuration import BaseConfiguration


def pool_creator(results: PoolResults, configuration: BaseConfiguration, game: GameDescription) -> None:
    assert isinstance(configuration, BlankConfiguration)

    results.to_place.append(create_generated_pickup("Victory Key", game.resource_database))
