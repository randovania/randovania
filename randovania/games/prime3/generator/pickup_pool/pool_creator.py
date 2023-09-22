from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.prime3.generator.pickup_pool.energy_cells import add_energy_cells
from randovania.games.prime3.layout.corruption_configuration import CorruptionConfiguration

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.generator.pickup_pool import PoolResults
    from randovania.layout.base.base_configuration import BaseConfiguration


def corruption_specific_pool(results: PoolResults, configuration: BaseConfiguration, game: GameDescription) -> None:
    assert isinstance(configuration, CorruptionConfiguration)
    # Adding Energy Cells to pool
    results.extend_with(add_energy_cells(game.resource_database))
