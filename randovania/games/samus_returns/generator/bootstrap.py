from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.samus_returns.layout.msr_configuration import MSRConfiguration
from randovania.resolver.bootstrap import MetroidBootstrap

if TYPE_CHECKING:
    from randovania.game_description.resources.resource_database import ResourceDatabase
    from randovania.game_description.resources.resource_info import ResourceGain
    from randovania.layout.base.base_configuration import BaseConfiguration


class MSRBootstrap(MetroidBootstrap):
    def _get_enabled_misc_resources(
        self, configuration: BaseConfiguration, resource_database: ResourceDatabase
    ) -> set[str]:
        enabled_resources = set()
        assert isinstance(configuration, MSRConfiguration)

        logical_patches = {
            "allow_highly_dangerous_logic": "HighDanger",
            "nerf_power_bombs": "NerfPBs",
            "nerf_super_missiles": "NerfSupers",
            "surface_crumbles": "SurfaceCrumbles",
            "area1_crumbles": "Area1Crumbles",
        }
        for name, index in logical_patches.items():
            if getattr(configuration, name):
                enabled_resources.add(index)

        return enabled_resources

    def event_resources_for_configuration(
        self,
        configuration: BaseConfiguration,
        resource_database: ResourceDatabase,
    ) -> ResourceGain:
        assert isinstance(configuration, MSRConfiguration)

        if configuration.elevator_grapple_blocks:
            for name in [
                "Area 4 (West) - Transport Area Grapple Block Pull Right",
                "Area 5 (Entrance) - Chozo Seal Grapple Block Bottom",
                "Area 6 - Transport to Area 7 Grapple Block Pull",
                "Area 7 - Transport to Area 8 Grapple Block",
            ]:
                yield resource_database.get_event(name), 1

        if configuration.area3_interior_shortcut_no_grapple:
            yield resource_database.get_event(
                "Area 3 (Interior East) - Transport to Area 3 Interior West Grapple Block"
            ), 1
