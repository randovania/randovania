from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.generator.base_patches_factory import BasePatchesFactory
from randovania.generator.teleporter_distributor import (
    get_dock_connections_assignment_for_teleporter,
    get_teleporter_connections,
)

if TYPE_CHECKING:
    from collections.abc import Iterable
    from random import Random

    from game_description.db.dock_node import DockNode
    from game_description.game_description import GameDescription
    from games.samus_returns.layout.msr_configuration import MSRConfiguration

    from randovania.game_description.db.node import Node


class MSRBasePatchesFactory(BasePatchesFactory):
    def dock_connections_assignment(
        self, configuration: MSRConfiguration, game: GameDescription, rng: Random
    ) -> Iterable[tuple[DockNode, Node]]:
        teleporter_connection = get_teleporter_connections(configuration.teleporters, game, rng)
        dock_assignment = get_dock_connections_assignment_for_teleporter(
            configuration.teleporters, game, teleporter_connection
        )
        yield from dock_assignment
