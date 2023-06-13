import dataclasses

from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import ResourceCollection
from randovania.layout.base.base_configuration import BaseConfiguration
from randovania.resolver.bootstrap import MetroidBootstrap


class AM2RBootstrap(MetroidBootstrap):
    def _get_enabled_misc_resources(self, configuration: BaseConfiguration,
                                    resource_database: ResourceDatabase) -> set[str]:

        enabled_resources = set()

        logical_patches = {
            "septogg_helpers": "Septogg",
            "change_level_design": "LevelDesign",
            "skip_cutscenes": "SkipCutscenes",
            "respawn_bomb_blocks": "RespawnBombBlocks"
        }

        for name, index in logical_patches.items():
            if getattr(configuration, name):
                enabled_resources.add(index)

        return enabled_resources

    def _damage_reduction(self, db: ResourceDatabase, current_resources: ResourceCollection):
        num_suits = sum(current_resources[db.get_item_by_name(suit)]
                        for suit in ["Varia Suit", "Gravity Suit"])
        return 2 ** (-num_suits)

    def patch_resource_database(self, db: ResourceDatabase, configuration: BaseConfiguration) -> ResourceDatabase:
        base_damage_reduction = self._damage_reduction

        return dataclasses.replace(db, base_damage_reduction=base_damage_reduction)
