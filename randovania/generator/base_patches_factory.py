from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.game_description.game_patches import GamePatches
from randovania.game_description.hint import HintItemPrecision, HintLocationPrecision
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.generator.pickup_pool import pool_creator
from randovania.layout.exceptions import InvalidConfiguration

if TYPE_CHECKING:
    from collections.abc import Iterable
    from random import Random

    from randovania.game_description.db.dock_node import DockNode
    from randovania.game_description.db.node import Node
    from randovania.game_description.db.node_identifier import NodeIdentifier
    from randovania.game_description.game_description import GameDescription
    from randovania.layout.base.base_configuration import BaseConfiguration


class MissingRng(Exception):
    pass


HintTargetPrecision = tuple[PickupIndex, HintLocationPrecision, HintItemPrecision]


class BasePatchesFactory[Configuration: BaseConfiguration]:
    def apply_static_configuration_patches(
        self, configuration: Configuration, game: GameDescription, initial_patches: GamePatches
    ) -> GamePatches:
        """
        Allows games to apply their own static (non-randomized) patches based on the configuration.
        """
        return initial_patches

    def create_static_base_patches(
        self, configuration: Configuration, game: GameDescription, player_index: int
    ) -> GamePatches:
        """
        Creates game patches that are intrinsic to the game's configuration, before any randomization
        has been applied.

        This can be used by trackers to ensure they have the same information about a generated game
        that the player would have based on the preset itself, before actually playing the seed.
        """
        patches = GamePatches.create_from_game(game, player_index, configuration)
        patches = self.apply_static_configuration_patches(configuration, game, patches)

        return patches

    def create_base_patches(
        self,
        configuration: Configuration,
        rng: Random,
        game: GameDescription,
        is_multiworld: bool,
        player_index: int,
        rng_required: bool = True,
    ) -> GamePatches:
        """ """
        patches = self.create_static_base_patches(configuration, game, player_index)

        # Teleporters
        try:
            patches = patches.assign_dock_connections(self.dock_connections_assignment(configuration, game, rng))
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

        try:
            patches = patches.assign_game_specific(self.create_game_specific(configuration, game, rng))
        except MissingRng as e:
            if rng_required:
                raise e

        # Check Item Pool
        self.check_item_pool(configuration)

        return patches

    def check_item_pool(self, configuration: Configuration) -> None:
        """
        Raises an InvalidConfiguration Exception if there are more items in the pool than allowed
        :param configuration:
        :return:
        """
        per_category_pool = pool_creator.calculate_pool_pickup_count(configuration)
        pool_items, maximum_size = pool_creator.get_total_pickup_count(per_category_pool)
        if pool_items > maximum_size:
            raise InvalidConfiguration(
                f"{pool_items} items in the pool, but only {maximum_size} are allowed at maximum"
            )

    def dock_connections_assignment(
        self, configuration: Configuration, game: GameDescription, rng: Random
    ) -> Iterable[tuple[DockNode, Node]]:
        """
        Adds dock connections if a game's patcher factory overwrites it. e.g. add teleporters
        :param configuration:
        :param game:
        :param rng:
        :return:
        """
        yield from []

    def starting_location_for_configuration(
        self,
        configuration: Configuration,
        game: GameDescription,
        rng: Random,
    ) -> NodeIdentifier:
        locations = list(configuration.starting_location.locations)
        if len(locations) == 0:
            raise InvalidConfiguration("No starting locations are selected!")
        elif len(locations) == 1:
            location = locations[0]
        else:
            if rng is None:
                raise MissingRng("Starting Location")
            location = rng.choice(locations)

        return location

    def create_game_specific(self, configuration: Configuration, game: GameDescription, rng: Random) -> dict:
        return {}
