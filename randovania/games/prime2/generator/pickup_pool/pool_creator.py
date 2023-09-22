from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.prime2.generator.pickup_pool.dark_temple_keys import add_dark_temple_keys
from randovania.games.prime2.generator.pickup_pool.sky_temple_keys import add_sky_temple_key_distribution_logic
from randovania.games.prime2.layout.echoes_configuration import EchoesConfiguration

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.generator.pickup_pool import PoolResults
    from randovania.layout.base.base_configuration import BaseConfiguration


def echoes_specific_pool(results: PoolResults, configuration: BaseConfiguration, game: GameDescription):
    assert isinstance(configuration, EchoesConfiguration)
    # Adding Dark Temple Keys to pool
    results.extend_with(add_dark_temple_keys(game.resource_database))

    # Adding Sky Temple Keys to pool
    results.extend_with(add_sky_temple_key_distribution_logic(game, configuration.sky_temple_keys))
