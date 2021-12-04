import copy
import dataclasses
from random import Random
from typing import Union

from randovania.game_description import default_database
from randovania.game_description.assignment import NodeConfigurationAssignment
from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.world.area_identifier import AreaIdentifier
from randovania.game_description.world.world_list import WorldList
from randovania.generator import elevator_distributor
from randovania.layout.base.base_configuration import BaseConfiguration
from randovania.layout.lib.teleporters import TeleporterShuffleMode
from randovania.games.prime2.layout.echoes_configuration import EchoesConfiguration


class MissingRng(Exception):
    pass

class BasePatchesFactory:
    def create_base_patches(self,
                            configuration: BaseConfiguration,
                            rng: Random,
                            game: GameDescription,
                            is_multiworld: bool,
                            player_index: int,
                            ) -> GamePatches:
        """
        """
        patches = dataclasses.replace(game.create_game_patches(),
                                    player_index=player_index)

        # Elevators
        patches = self.add_elevator_connections_to_patches(configuration, rng, patches)

        # Configurable Nodes
        patches = patches.assign_node_configuration(
            self.configurable_node_assignment(configuration, game, rng)
        )

        # Starting Location
        patches = patches.assign_starting_location(
            self.starting_location_for_configuration(configuration, game, rng))

        # Hints
        if rng is not None:
            patches = self.add_default_hints_to_patches(rng, patches, game.world_list,
                                                        num_joke=self.num_joke_hints, is_multiworld=is_multiworld)

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
                                            ) -> AreaIdentifier:
        locations = list(configuration.starting_location.locations)
        if len(locations) == 0:
            raise ValueError("No available starting locations")
        elif len(locations) == 1:
            location = locations[0]
        else:
            if rng is None:
                raise MissingRng("Starting Location")
            location = rng.choice(locations)

        return location
    
    def configurable_node_assignment(self, configuration: BaseConfiguration, game: GameDescription, rng: Random) -> NodeConfigurationAssignment:
        return NodeConfigurationAssignment()

    @property
    def num_joke_hints(self) -> int:
        return 2

    def add_default_hints_to_patches(self, rng: Random, patches: GamePatches, world_list: WorldList, num_joke: int, is_multiworld: bool) -> GamePatches:
        """
        Adds hints that are present on all games.
        :param rng:
        :param patches:
        :param world_list:
        :param num_joke
        :param is_multiworld
        :return:
        """
        return patches

class PrimeTrilogyBasePatchesFactory(BasePatchesFactory):
    def add_elevator_connections_to_patches(self, configuration: EchoesConfiguration, rng: Random, patches: GamePatches) -> GamePatches:
        elevator_connection = copy.copy(patches.elevator_connection)
        elevators = configuration.elevators

        if not elevators.is_vanilla:
            if rng is None:
                raise MissingRng("Elevator")

            world_list = default_database.game_description_for(configuration.game).world_list
            elevator_db = elevator_distributor.create_elevator_database(
                world_list, elevators.editable_teleporters)

            if elevators.mode in {TeleporterShuffleMode.TWO_WAY_RANDOMIZED, TeleporterShuffleMode.TWO_WAY_UNCHECKED}:
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

        return dataclasses.replace(patches, elevator_connection=elevator_connection)
