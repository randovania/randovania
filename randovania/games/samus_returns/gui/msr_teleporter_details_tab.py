from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.samus_returns.layout.msr_configuration import MSRConfiguration
from randovania.gui.game_details.teleporter_details_tab import TeleporterDetailsTab

if TYPE_CHECKING:
    from randovania.game_description.game_patches import GamePatches
    from randovania.interface_common.players_configuration import PlayersConfiguration
    from randovania.layout.base.base_configuration import BaseConfiguration


class MSRTeleporterDetailsTab(TeleporterDetailsTab):
    @classmethod
    def should_appear_for(
        cls, configuration: BaseConfiguration, all_patches: dict[int, GamePatches], players: PlayersConfiguration
    ) -> bool:
        assert isinstance(configuration, MSRConfiguration)
        return not configuration.teleporters.is_vanilla

    def tab_title(self) -> str:
        return "Elevators"
