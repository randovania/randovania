from __future__ import annotations

from random import Random
from typing import TYPE_CHECKING

from randovania.game_description import default_database
from randovania.layout import filtered_database

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.pickup.pickup_database import PickupDatabase
    from randovania.games.game import RandovaniaGame
    from randovania.interface_common.players_configuration import PlayersConfiguration
    from randovania.layout.base.base_configuration import BaseConfiguration
    from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches
    from randovania.layout.layout_description import LayoutDescription


class BasePatchDataFactory:
    description: LayoutDescription
    players_config: PlayersConfiguration
    game: GameDescription
    pickup_db: PickupDatabase
    patches: GamePatches
    rng: Random

    cosmetic_patches: BaseCosmeticPatches
    configuration: BaseConfiguration

    def __init__(self, description: LayoutDescription, players_config: PlayersConfiguration,
                 cosmetic_patches: BaseCosmeticPatches):
        self.description = description
        self.players_config = players_config
        self.cosmetic_patches = cosmetic_patches

        self.pickup_db = default_database.pickup_database_for_game(self.game_enum())

        self.patches = description.all_patches[players_config.player_index]
        self.configuration = description.get_preset(players_config.player_index).configuration
        self.rng = Random(description.get_seed_for_player(players_config.player_index))
        self.game = filtered_database.game_description_for_layout(self.configuration)

    def game_enum(self) -> RandovaniaGame:
        raise NotImplementedError

    def create_data(self) -> dict:
        raise NotImplementedError
