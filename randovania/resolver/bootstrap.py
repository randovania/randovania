from typing import NamedTuple

from randovania.game_description import default_database
from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import ResourceGain, ResourceCollection
from randovania.game_description.world.node import NodeContext
from randovania.game_description.world.resource_node import ResourceNode
from randovania.layout.base.base_configuration import BaseConfiguration
from randovania.layout.base.major_items_configuration import MajorItemsConfiguration
from randovania.layout.base.trick_level import LayoutTrickLevel
from randovania.layout.base.trick_level_configuration import TrickLevelConfiguration
from randovania.resolver.state import State, StateGameData


class EnergyConfig(NamedTuple):
    starting_energy: int
    energy_per_tank: int


class Bootstrap:
    def trick_resources_for_configuration(self, configuration: TrickLevelConfiguration,
                                          resource_database: ResourceDatabase,
                                          ) -> ResourceGain:
        """
        :param configuration:
        :param resource_database:
        :return:
        """

        static_resources = {}

        for trick in resource_database.trick:
            if configuration.minimal_logic:
                level = LayoutTrickLevel.maximum()
            else:
                level = configuration.level_for_trick(trick)

            yield trick, level.as_number

        return static_resources

    def event_resources_for_configuration(self, configuration: BaseConfiguration,
                                          resource_database: ResourceDatabase,
                                          ) -> ResourceGain:
        yield from []

    def _add_minimal_logic_initial_resources(self, resources: ResourceCollection,
                                             game: GameDescription,
                                             major_items: MajorItemsConfiguration,
                                             ) -> None:
        resource_database = game.resource_database

        if game.minimal_logic is None:
            raise ValueError(f"Minimal logic enabled, but {game.game} doesn't have support for it.")

        item_db = default_database.item_database_for_game(game.game)

        items_to_skip = set()
        for it in game.minimal_logic.items_to_exclude:
            if it.reason is None or major_items.items_state[item_db.major_items[it.reason]].num_shuffled_pickups != 0:
                items_to_skip.add(it.name)

        custom_item_count = game.minimal_logic.custom_item_amount
        events_to_skip = {it.name for it in game.minimal_logic.events_to_exclude}

        resources.add_resource_gain([
            (event, 1)
            for event in resource_database.event
            if event.short_name not in events_to_skip
        ])

        resources.add_resource_gain([
            (item, custom_item_count.get(item.short_name, 1))
            for item in resource_database.item
            if item.short_name not in items_to_skip
        ])

    def energy_config(self, configuration: BaseConfiguration) -> EnergyConfig:
        return EnergyConfig(99, 100)

    def calculate_starting_state(self, game: GameDescription, patches: GamePatches,
                                 configuration: BaseConfiguration) -> "State":
        starting_node = game.world_list.resolve_teleporter_connection(patches.starting_location)
        initial_resources = patches.starting_items.duplicate()

        starting_energy, energy_per_tank = self.energy_config(configuration)

        if starting_node.is_resource_node:
            assert isinstance(starting_node, ResourceNode)
            initial_resources.add_resource_gain(
                starting_node.resource_gain_on_collect(NodeContext(
                    patches, initial_resources,
                    game.resource_database, game.world_list,
                )),
            )

        initial_game_state = game.initial_states.get("Default")
        if initial_game_state is not None:
            initial_resources.add_resource_gain(initial_game_state)

        starting_state = State(
            initial_resources,
            (),
            None,
            starting_node,
            patches,
            None,
            StateGameData(
                game.resource_database,
                game.world_list,
                energy_per_tank,
                starting_energy
            )
        )

        # Being present with value 0 is troublesome since this dict is used for a simplify_requirements later on
        keys_to_remove = [resource
                          for resource, quantity in initial_resources.as_resource_gain()
                          if quantity == 0]
        for resource in keys_to_remove:
            initial_resources.remove_resource(resource)

        return starting_state

    def version_resources_for_game(self, configuration: BaseConfiguration,
                                   resource_database: ResourceDatabase) -> ResourceGain:
        """
        Determines which Version resources should be enabled, according to the configuration.
        Override as needed.
        """
        # Only enable one specific version
        for resource in resource_database.version:
            yield resource, 1 if resource.long_name == "NTSC" else 0

    def _get_enabled_misc_resources(self, configuration: BaseConfiguration, resource_database: ResourceDatabase) -> set[
        str]:
        """
        Returns a set of strings corresponding to Misc resource short names which should be enabled.
        Override as needed.
        """
        return set()

    def misc_resources_for_configuration(self, configuration: BaseConfiguration,
                                         resource_database: ResourceDatabase) -> ResourceGain:
        """
        Determines which Misc resources should be enabled, according to the configuration.
        """
        enabled_resources = self._get_enabled_misc_resources(configuration, resource_database)
        for resource in resource_database.misc:
            yield resource, 1 if resource.short_name in enabled_resources else 0

    def patch_resource_database(self, db: ResourceDatabase, configuration: BaseConfiguration) -> ResourceDatabase:
        """
        Makes modifications to the resource database according to the configuration.
        Requirement templates and damage reductions are common candidates for modification.
        Override as needed.
        """
        return db

    def logic_bootstrap(self,
                        configuration: BaseConfiguration,
                        game: GameDescription,
                        patches: GamePatches,
                        ) -> tuple[GameDescription, State]:
        """
        Core code for starting a new Logic/State.
        :param configuration:
        :param game:
        :param patches:
        :return:
        """
        if not game.mutable:
            raise ValueError("Running logic_bootstrap with non-mutable game")

        game.world_list.ensure_has_node_cache()
        starting_state = self.calculate_starting_state(game, patches, configuration)

        if configuration.trick_level.minimal_logic:
            self._add_minimal_logic_initial_resources(starting_state.resources,
                                                      game,
                                                      configuration.major_items_configuration)

        static_resources = ResourceCollection.with_database(game.resource_database)
        static_resources.add_resource_gain(
            self.trick_resources_for_configuration(configuration.trick_level, game.resource_database)
        )
        static_resources.add_resource_gain(
            self.event_resources_for_configuration(configuration, game.resource_database)
        )
        static_resources.add_resource_gain(
            self.version_resources_for_game(configuration, game.resource_database)
        )
        static_resources.add_resource_gain(
            self.misc_resources_for_configuration(configuration, game.resource_database)
        )

        for resource, quantity in static_resources.as_resource_gain():
            starting_state.resources.set_resource(resource, quantity)

        game.patch_requirements(starting_state.resources, configuration.damage_strictness.value)

        return game, starting_state


class MetroidBootstrap(Bootstrap):
    def energy_config(self, configuration: BaseConfiguration) -> EnergyConfig:
        return EnergyConfig(configuration.energy_per_tank - 1, configuration.energy_per_tank)
