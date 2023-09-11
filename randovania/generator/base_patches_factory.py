from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.game_description.game_patches import GamePatches
from randovania.game_description.hint import HintItemPrecision, HintLocationPrecision
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.layout.exceptions import InvalidConfiguration

if TYPE_CHECKING:
    from collections.abc import Iterable
    from random import Random

    from randovania.game_description.assignment import NodeConfigurationAssociation
    from randovania.game_description.db.dock_node import DockNode
    from randovania.game_description.db.node import Node
    from randovania.game_description.db.node_identifier import NodeIdentifier
    from randovania.game_description.game_description import GameDescription
    from randovania.layout.base.base_configuration import BaseConfiguration


class MissingRng(Exception):
    pass


HintTargetPrecision = tuple[PickupIndex, HintLocationPrecision, HintItemPrecision]


class BasePatchesFactory:
    def create_base_patches(
        self,
        configuration: BaseConfiguration,
        rng: Random,
        game: GameDescription,
        is_multiworld: bool,
        player_index: int,
        rng_required: bool = True,
    ) -> GamePatches:
        """ """
        patches = GamePatches.create_from_game(game, player_index, configuration)

        # Teleporters
        try:
            patches = patches.assign_dock_connections(self.dock_connections_assignment(configuration, game, rng))
        except MissingRng as e:
            if rng_required:
                raise e

        # Configurable Nodes
        try:
            patches = patches.assign_node_configuration(self.configurable_node_assignment(configuration, game, rng))
        except MissingRng as e:
            if rng_required:
                raise e

        # Starting Location
        try:
            patches = patches.assign_starting_location(
                self.starting_location_for_configuration(configuration, game, rng)
            )
        except MissingRng as e:
            if rng_required:
                raise e

        return patches

    def dock_connections_assignment(
        self, configuration: BaseConfiguration, game: GameDescription, rng: Random
    ) -> Iterable[tuple[DockNode, Node]]:
        """
        Adds dock connections if a game's patcher factory overwrites it. e.g. add teleporters
        :param configuration:
        :param rng:
        :param patches:
        :return:
        """
        yield from []

    def starting_location_for_configuration(
        self,
        configuration: BaseConfiguration,
        game: GameDescription,
        rng: Random,
    ) -> NodeIdentifier:
        locations = list(configuration.starting_location.locations)
        if len(locations) == 0:
            raise InvalidConfiguration("No starting locations are selected")
        elif len(locations) == 1:
            location = locations[0]
        else:
            if rng is None:
                raise MissingRng("Starting Location")
            location = rng.choice(locations)

        return location

    def configurable_node_assignment(
        self,
        configuration: BaseConfiguration,
        game: GameDescription,
        rng: Random,
    ) -> Iterable[NodeConfigurationAssociation]:
        yield from []
