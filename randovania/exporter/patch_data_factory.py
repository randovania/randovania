from __future__ import annotations

import typing
from random import Random
from typing import TYPE_CHECKING

import json_delta

from randovania.exporter import pickup_exporter
from randovania.game_description import default_database
from randovania.game_description.assignment import PickupTarget
from randovania.generator.pickup_pool import pickup_creator
from randovania.layout import filtered_database

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.pickup.pickup_database import PickupDatabase
    from randovania.game_description.pickup.pickup_entry import PickupEntry
    from randovania.games.game import RandovaniaGame
    from randovania.interface_common.players_configuration import PlayersConfiguration
    from randovania.layout.base.base_configuration import BaseConfiguration
    from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches
    from randovania.layout.layout_description import LayoutDescription


class PatcherDataMeta(typing.TypedDict):
    layout_was_user_modified: bool


class PatchDataFactory:
    description: LayoutDescription
    players_config: PlayersConfiguration
    game: GameDescription
    pickup_db: PickupDatabase
    patches: GamePatches
    rng: Random

    cosmetic_patches: BaseCosmeticPatches
    configuration: BaseConfiguration

    def __init__(
        self,
        description: LayoutDescription,
        players_config: PlayersConfiguration,
        cosmetic_patches: BaseCosmeticPatches,
    ):
        self.description = description
        self.players_config = players_config
        self.cosmetic_patches = cosmetic_patches

        self.pickup_db = default_database.pickup_database_for_game(self.game_enum())

        self.patches = description.all_patches[players_config.player_index]
        self.configuration = description.get_preset(players_config.player_index).configuration
        self.rng = Random(description.get_seed_for_player(players_config.player_index))
        self.game = filtered_database.game_description_for_layout(self.configuration)
        self.memo_data = self.create_memo_data()

    def game_enum(self) -> RandovaniaGame:
        raise NotImplementedError

    def create_game_specific_data(self) -> dict:
        raise NotImplementedError

    def create_data(self) -> dict:
        game_data = self.create_game_specific_data()
        json_delta.patch(game_data, self.patches.custom_patcher_data)
        game_data["_randovania_meta"] = {
            "layout_was_user_modified": self.description.user_modified,
        }
        return game_data

    def create_memo_data(self) -> dict:
        """Used to generate pickup collection messages."""
        return pickup_exporter.GenericAcquiredMemo()

    def create_useless_pickup(self) -> PickupEntry:
        """Used for any location with no PickupEntry assigned to it."""
        return pickup_creator.create_nothing_pickup(self.game.resource_database)

    def create_visual_nothing(self) -> PickupEntry:
        """The model of this pickup replaces the model of all pickups when PickupModelDataSource is ETM"""
        return pickup_creator.create_visual_nothing(self.game_enum())

    def export_pickup_list(self) -> list[pickup_exporter.ExportedPickupDetails]:
        """
        Processes all logic behind nothing pickups, hidden models, collection text and multiworld text into
        an easier to handle data structure.
        """
        return pickup_exporter.export_all_indices(
            self.patches,
            PickupTarget(self.create_useless_pickup(), self.players_config.player_index),
            self.game.region_list,
            self.rng,
            self.configuration.pickup_model_style,
            self.configuration.pickup_model_data_source,
            pickup_exporter.create_pickup_exporter(self.memo_data, self.players_config, self.game_enum()),
            self.create_visual_nothing(),
        )
