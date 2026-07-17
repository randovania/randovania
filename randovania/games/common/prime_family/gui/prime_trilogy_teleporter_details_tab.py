from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.prime1.layout.prime_configuration import PrimeConfiguration
from randovania.games.prime2.layout.echoes_configuration import EchoesConfiguration
from randovania.games.prime2_opr.layout.prime2_opr_configuration import EchoesOPRConfiguration
from randovania.gui.game_details.teleporter_details_tab import TeleporterDetailsTab

if TYPE_CHECKING:
    from randovania.game_description.game_patches import GamePatches
    from randovania.interface_common.players_configuration import PlayersConfiguration


class PrimeTrilogyTeleporterDetailsTab(
    TeleporterDetailsTab[PrimeConfiguration | EchoesConfiguration | EchoesOPRConfiguration]
):
    @classmethod
    def should_appear_for(
        cls,
        configuration: PrimeConfiguration | EchoesConfiguration | EchoesOPRConfiguration,
        all_patches: dict[int, GamePatches],
        players: PlayersConfiguration,
    ) -> bool:
        return not configuration.teleporters.is_vanilla

    def tab_title(self) -> str:
        return "Elevators"
