from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import CurrentResources
from randovania.game_description.resources.resource_type import ResourceType
from randovania.games.dread.layout.dread_configuration import DreadConfiguration
from randovania.layout.base.base_configuration import BaseConfiguration
from randovania.resolver.bootstrap import MetroidBootstrap


class DreadBootstrap(MetroidBootstrap):
    def event_resources_for_configuration(self, configuration: BaseConfiguration,
                                          resource_database: ResourceDatabase,
                                          ) -> CurrentResources:
        assert isinstance(configuration, DreadConfiguration)
        result = {}

        if configuration.hanubia_shortcut_no_grapple:
            for name in ["s080_shipyard:default:grapplepulloff1x2_000", "s080_shipyard:default:grapplepulloff1x2"]:
                result[resource_database.get_by_type_and_index(ResourceType.EVENT, name)] = 1

        return result
