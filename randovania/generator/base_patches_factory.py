from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.game_description.db.dock_node import DockNode
from randovania.game_description.game_patches import ElevatorConnection, GamePatches
from randovania.game_description.hint import HintItemPrecision, HintLocationPrecision
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.prime1.layout.prime_configuration import PrimeConfiguration
from randovania.games.prime2.layout.echoes_configuration import EchoesConfiguration
from randovania.games.prime3.layout.corruption_configuration import CorruptionConfiguration
from randovania.generator import elevator_distributor
from randovania.layout import filtered_database
from randovania.layout.exceptions import InvalidConfiguration
from randovania.layout.lib.teleporters import TeleporterShuffleMode

if TYPE_CHECKING:
    from collections.abc import Iterable
    from random import Random

    from randovania.game_description.assignment import NodeConfigurationAssociation
    from randovania.game_description.db.node_identifier import NodeIdentifier
    from randovania.game_description.game_description import GameDescription
    from randovania.layout.base.base_configuration import BaseConfiguration


class MissingRng(Exception):
    pass


HintTargetPrecision = tuple[PickupIndex, HintLocationPrecision, HintItemPrecision]


class BasePatchesFactory:
    def create_base_patches(self,
                            configuration: BaseConfiguration,
                            rng: Random,
                            game: GameDescription,
                            is_multiworld: bool,
                            player_index: int,
                            rng_required: bool = True
                            ) -> GamePatches:
        """
        """
        patches = GamePatches.create_from_game(game, player_index, configuration)

        # Elevators
        try:
            patches = self.add_elevator_connections_to_patches(configuration, rng, patches)
        except MissingRng as e:
            if rng_required:
                raise e

        # Configurable Nodes
        try:
            patches = patches.assign_node_configuration(
                self.configurable_node_assignment(configuration, game, rng)
            )
        except MissingRng as e:
            if rng_required:
                raise e

        # Starting Location
        try:
            patches = patches.assign_starting_location(
                self.starting_location_for_configuration(configuration, game, rng))
        except MissingRng as e:
            if rng_required:
                raise e

        return patches

    def add_elevator_connections_to_patches(self,
                                            configuration: BaseConfiguration,
                                            rng: Random,
                                            patches: GamePatches) -> GamePatches:
        """
        Changes the connections between Teleporter nodes.
        :param configuration:
        :param rng:
        :param patches:
        :return:
        """
        return patches

    def starting_location_for_configuration(self,
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

    def configurable_node_assignment(self, configuration: BaseConfiguration, game: GameDescription, rng: Random,
                                     ) -> Iterable[NodeConfigurationAssociation]:
        yield from []


TrilogyConfiguration = PrimeConfiguration | EchoesConfiguration | CorruptionConfiguration


class PrimeTrilogyBasePatchesFactory(BasePatchesFactory):
    def add_elevator_connections_to_patches(self, configuration: TrilogyConfiguration, rng: Random,
                                            patches: GamePatches) -> GamePatches:
        elevators = configuration.elevators

        game_description = filtered_database.game_description_for_layout(configuration)
        region_list = game_description.region_list
        elevator_connection: ElevatorConnection = {}

        if not elevators.is_vanilla:
            if rng is None:
                raise MissingRng("Elevator")

            elevator_dock_types = game_description.dock_weakness_database.all_teleporter_dock_types
            elevator_db = elevator_distributor.create_elevator_database(region_list, elevators.editable_teleporters,
                                                                        elevator_dock_types)
            if elevators.mode == TeleporterShuffleMode.ECHOES_SHUFFLED:
                connections = self.elevator_echoes_shuffled(configuration, patches, rng)

            elif elevators.mode in {TeleporterShuffleMode.TWO_WAY_RANDOMIZED, TeleporterShuffleMode.TWO_WAY_UNCHECKED}:
                connections = elevator_distributor.two_way_elevator_connections(
                    rng=rng,
                    elevator_database=elevator_db,
                    between_areas=elevators.mode == TeleporterShuffleMode.TWO_WAY_RANDOMIZED
                )
            else:
                connections = elevator_distributor.one_way_elevator_connections(
                    rng=rng,
                    elevator_database=elevator_db,
                    target_locations=elevators.valid_targets,
                    replacement=elevators.mode != TeleporterShuffleMode.ONE_WAY_ELEVATOR,
                )

            elevator_connection.update(connections)

        for teleporter, destination in elevators.static_teleporters.items():
            elevator_connection[teleporter] = destination

        assignment = [
            (region_list.typed_node_by_identifier(identifier, DockNode), region_list.node_by_identifier(target))
            for identifier, target in elevator_connection.items()
        ]

        return patches.assign_dock_connections(assignment)

    def elevator_echoes_shuffled(self, configuration: TrilogyConfiguration, patches: GamePatches,
                                 rng: Random) -> ElevatorConnection:
        raise InvalidConfiguration("Incompatible elevator mode for this game")
