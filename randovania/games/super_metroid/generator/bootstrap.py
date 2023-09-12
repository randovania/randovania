from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from randovania.games.super_metroid.layout.super_metroid_configuration import SuperMetroidConfiguration
from randovania.resolver.bootstrap import MetroidBootstrap

if TYPE_CHECKING:
    from randovania.game_description.resources.resource_collection import ResourceCollection
    from randovania.game_description.resources.resource_database import ResourceDatabase
    from randovania.layout.base.base_configuration import BaseConfiguration


class SuperMetroidBootstrap(MetroidBootstrap):
    def _get_enabled_misc_resources(
        self, configuration: BaseConfiguration, resource_database: ResourceDatabase
    ) -> set[str]:
        assert isinstance(configuration, SuperMetroidConfiguration)

        enabled_resources = set()

        logical_patches = {
            "dachora_pit": "DachoraPitTweaks",
            "early_supers_bridge": "SupersBridgeTweaks",
            "pre_hi_jump": "PreHijumpTweaks",
            "moat": "MoatTweaks",
            "pre_spazer": "PreSpazerTweaks",
            "red_tower": "RedTowerTweaks",
            "nova_boost_platform": "NovaBoostTweaks",
            "cant_use_supers_on_red_doors": "CantUseSupersOnRedDoors",
            "nerfed_rainbow_beam": "MBRainbowBeamNerf",
            "no_ln_chozo_inventory_check": "NoLowerNorfairInventoryCheck",
        }

        for name, index in logical_patches.items():
            if getattr(configuration.patches, name):
                enabled_resources.add(index)

        return enabled_resources

    def _damage_reduction(self, db: ResourceDatabase, current_resources: ResourceCollection):
        num_suits = sum(current_resources[db.get_item_by_name(suit)] for suit in ["Varia Suit", "Gravity Suit"])
        return 2 ** (-num_suits)

    def patch_resource_database(self, db: ResourceDatabase, configuration: BaseConfiguration) -> ResourceDatabase:
        base_damage_reduction = self._damage_reduction

        return dataclasses.replace(db, base_damage_reduction=base_damage_reduction)
