from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.pseudoregalia.layout.pseudoregalia_configuration import PseudoregaliaConfiguration

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.generator.pickup_pool import PoolResults
    from randovania.layout.base.base_configuration import BaseConfiguration


def pool_creator(results: PoolResults, configuration: BaseConfiguration, game: GameDescription) -> None:
    assert isinstance(configuration, PseudoregaliaConfiguration)
