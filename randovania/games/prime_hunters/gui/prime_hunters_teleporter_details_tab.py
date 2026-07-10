from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.prime_hunters.layout.prime_hunters_configuration import HuntersConfiguration
from randovania.gui.game_details.teleporter_details_tab import TeleporterDetailsTab

if TYPE_CHECKING:
    from randovania.game_description.game_patches import GamePatches
    from randovania.interface_common.players_configuration import PlayersConfiguration


class HuntersTeleporterDetailsTab(TeleporterDetailsTab[HuntersConfiguration]):
    @classmethod
    def should_appear_for(
        cls, configuration: HuntersConfiguration, all_patches: dict[int, GamePatches], players: PlayersConfiguration
    ) -> bool:
        return not configuration.teleporters.is_vanilla

    def tab_title(self) -> str:
        return "Portals"
