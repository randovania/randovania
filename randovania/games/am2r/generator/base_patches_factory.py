from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.generator.base_patches_factory import BasePatchesFactory
from randovania.generator.elevator_distributor import get_dock_connections_for_elevators

if TYPE_CHECKING:
    from collections.abc import Iterable
    from random import Random

    from randovania.game_description.db.dock_node import DockNode
    from randovania.game_description.db.node import Node
    from randovania.game_description.game_description import GameDescription
    from randovania.games.am2r.layout.am2r_configuration import AM2RConfiguration


class AM2RBasePatchesFactory(BasePatchesFactory):

    def dock_connections_assignment(self, configuration: AM2RConfiguration,
                                game: GameDescription, rng: Random ) -> Iterable[tuple[DockNode, Node]]:
        dock_assignment = get_dock_connections_for_elevators(configuration, game, rng)
        yield from dock_assignment
