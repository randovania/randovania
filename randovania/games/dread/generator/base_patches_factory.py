from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.game_description.db.dock_node import DockNode
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.games.dread.layout.dread_configuration import DreadConfiguration
from randovania.generator.base_patches_factory import BasePatchesFactory
from randovania.generator.teleporter_distributor import (
    get_dock_connections_assignment_for_teleporter,
    get_teleporter_connections,
)

if TYPE_CHECKING:
    from collections.abc import Iterable
    from random import Random

    from randovania.game_description.db.node import Node
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.game_patches import GamePatches


class DreadBasePatchesFactory(BasePatchesFactory[DreadConfiguration]):
    def apply_static_configuration_patches(
        self, configuration: DreadConfiguration, game: GameDescription, initial_patches: GamePatches
    ) -> GamePatches:
        dock_weakness = []
        if configuration.hanubia_easier_path_to_itorash:
            nic = NodeIdentifier.create
            power_weak = game.dock_weakness_database.get_by_weakness("door", "Power Beam Door")

            dock_weakness.extend(
                [
                    (nic("Hanubia", "Entrance Tall Room", "Door to Total Recharge Station North"), power_weak),
                    (nic("Hanubia", "Total Recharge Station North", "Door to Gold Chozo Warrior Arena"), power_weak),
                ]
            )

        return initial_patches.assign_dock_weakness(
            (
                (game.region_list.typed_node_by_identifier(identifier, DockNode), target)
                for identifier, target in dock_weakness
            )
        )

    def create_static_base_patches(
        self, configuration: DreadConfiguration, game: GameDescription, player_index: int
    ) -> GamePatches:
        return super().create_static_base_patches(configuration, game, player_index)

    def create_base_patches(
        self,
        configuration: DreadConfiguration,
        rng: Random,
        game: GameDescription,
        is_multiworld: bool,
        player_index: int,
        rng_required: bool = True,
    ) -> GamePatches:
        return super().create_base_patches(configuration, rng, game, is_multiworld, player_index, rng_required)

    def dock_connections_assignment(
        self, configuration: DreadConfiguration, game: GameDescription, rng: Random
    ) -> Iterable[tuple[DockNode, Node]]:
        teleporter_connection = get_teleporter_connections(configuration.teleporters, game, rng)
        dock_assignment = get_dock_connections_assignment_for_teleporter(
            configuration.teleporters, game, teleporter_connection
        )
        yield from dock_assignment
