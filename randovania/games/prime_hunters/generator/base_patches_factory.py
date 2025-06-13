from __future__ import annotations

from copy import copy
from typing import TYPE_CHECKING

from randovania.games.prime_hunters.layout import HuntersConfiguration
from randovania.games.prime_hunters.layout.force_field_configuration import LayoutForceFieldRequirement
from randovania.generator.base_patches_factory import BasePatchesFactory, MissingRng
from randovania.generator.teleporter_distributor import (
    get_dock_connections_assignment_for_teleporter,
    get_teleporter_connections,
)

if TYPE_CHECKING:
    from collections.abc import Iterable
    from random import Random

    from randovania.game_description.db.dock_node import DockNode
    from randovania.game_description.db.node import Node
    from randovania.game_description.game_description import GameDescription
    from randovania.layout.base.base_configuration import BaseConfiguration


class HuntersBasePatchesFactory(BasePatchesFactory[HuntersConfiguration]):
    def create_game_specific(self, configuration: HuntersConfiguration, game: GameDescription, rng: Random) -> dict:
        all_choices = list(LayoutForceFieldRequirement)
        all_choices.remove(LayoutForceFieldRequirement.RANDOM)
        without_removed = copy(all_choices)

        force_fields: dict = {}

        for identifier, requirement in configuration.force_field_configuration.force_field_requirement.items():
            if requirement == LayoutForceFieldRequirement.RANDOM:
                if rng is None:
                    raise MissingRng("Force Field")

                requirement = rng.choice(without_removed)

            force_fields[identifier.as_string] = requirement.value

        return {
            "force_fields": force_fields,
        }

    def dock_connections_assignment(
        self, configuration: BaseConfiguration, game: GameDescription, rng: Random
    ) -> Iterable[tuple[DockNode, Node]]:
        assert isinstance(configuration, HuntersConfiguration)
        teleporter_connection = get_teleporter_connections(configuration.teleporters, game, rng)
        dock_assignment = get_dock_connections_assignment_for_teleporter(
            configuration.teleporters, game, teleporter_connection
        )
        yield from dock_assignment
