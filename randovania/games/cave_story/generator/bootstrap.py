from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import CurrentResources
from randovania.games.cave_story.layout.cs_configuration import CSConfiguration, CSObjective
from randovania.resolver.bootstrap import Bootstrap, EnergyConfig


class CSBootstrap(Bootstrap):
    def _get_enabled_misc_resources(self, configuration: CSConfiguration,
                                    resource_database: ResourceDatabase) -> set[str]:
        enabled_resources = set()

        objectives = {
            CSObjective.BAD_ENDING: "badEnd",
            CSObjective.NORMAL_ENDING: "normalEnd",
            CSObjective.BEST_ENDING: "bestEnd",
            CSObjective.ALL_BOSSES: "allBosses",
            CSObjective.HUNDRED_PERCENT: "hundo"
        }
        enabled_resources.add(objectives[configuration.objective])

        enabled_resources.add("PONR")

        return enabled_resources

    def version_resources_for_game(self, configuration: CSConfiguration,
                                   resource_database: ResourceDatabase) -> CurrentResources:
        return {
            resource: 1 if resource.long_name == "Freeware" else 0
            for resource in resource_database.version
        }

    def energy_config(self, configuration: CSConfiguration) -> EnergyConfig:
        return EnergyConfig(configuration.starting_hp, 1)
