from __future__ import annotations

from typing import TYPE_CHECKING, override

from randovania.games.prime2 import dark_aether_helper
from randovania.gui.preset_settings.starting_area_tab import PresetMetroidStartingArea

if TYPE_CHECKING:
    from randovania.game_description.db.node_identifier import NodeIdentifier
    from randovania.games.common.elevators import NodeListGrouping


class PresetEchoesStartingArea(PresetMetroidStartingArea):
    @override
    def nodes_by_areas_by_region_from_locations(self, all_node_locations: list[NodeIdentifier]) -> NodeListGrouping:
        return dark_aether_helper.wrap_node_list_grouping(
            super().nodes_by_areas_by_region_from_locations(all_node_locations)
        )
