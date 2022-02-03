import copy
import dataclasses

from randovania.game_description.requirements import ResourceRequirement
from randovania.game_description.resources.damage_resource_info import DamageReduction
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import CurrentResources
from randovania.game_description.resources.resource_type import ResourceType
from randovania.layout.base.base_configuration import BaseConfiguration
from randovania.resolver.bootstrap import MetroidBootstrap


class deltaruneBootstrap(MetroidBootstrap):
    def _get_enabled_misc_resources(self, configuration: BaseConfiguration, resource_database: ResourceDatabase) -> set[
        str]:
        enabled_resources = set()

        logical_patches = {
        }
        for name, index in logical_patches.items():
            if getattr(configuration, name):
                enabled_resources.add(index)

        return enabled_resources

