from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import ResourceGain
from randovania.games.dread.layout.dread_configuration import DreadConfiguration
from randovania.layout.base.base_configuration import BaseConfiguration
from randovania.resolver.bootstrap import MetroidBootstrap


class DreadBootstrap(MetroidBootstrap):
    def event_resources_for_configuration(self, configuration: BaseConfiguration,
                                          resource_database: ResourceDatabase,
                                          ) -> ResourceGain:
        assert isinstance(configuration, DreadConfiguration)

        if configuration.hanubia_shortcut_no_grapple:
            for name in ["s080_shipyard:default:grapplepulloff1x2_000", "s080_shipyard:default:grapplepulloff1x2"]:
                yield resource_database.get_event(name), 1

        if configuration.hanubia_easier_path_to_itorash:
            yield resource_database.get_event("s080_shipyard:default:grapplepulloff1x2_001"), 1

        if configuration.x_starts_released:
            yield resource_database.get_event("ElunReleaseX"), 1
