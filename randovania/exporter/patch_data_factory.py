from __future__ import annotations

import typing
from random import Random
from typing import TYPE_CHECKING

import json_delta

from randovania.exporter import pickup_exporter
from randovania.exporter.hints.hint_exporter import HintExporter
from randovania.game_description import default_database
from randovania.game_description.assignment import PickupTarget
from randovania.generator.pickup_pool import pickup_creator
from randovania.layout import filtered_database

if TYPE_CHECKING:
    from randovania.exporter.hints.hint_namer import HintNamer
    from randovania.game.game_enum import RandovaniaGame
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.pickup.pickup_database import PickupDatabase
    from randovania.game_description.pickup.pickup_entry import PickupEntry
    from randovania.interface_common.players_configuration import PlayersConfiguration
    from randovania.layout.base.base_configuration import BaseConfiguration
    from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches
    from randovania.layout.layout_description import LayoutDescription


class PatcherDataMeta(typing.TypedDict):
    layout_was_user_modified: bool
    in_race_setting: bool


class PatchDataFactory[Configuration: BaseConfiguration, CosmeticPatches: BaseCosmeticPatches]:
    """
    Class with the purpose of creating a JSON-serializable dictionary from a randomized game.
    The resulting dictionary-data will later be passed to the patcher.
    Since every patcher needs their data laid out differently, it's up to
    each game to define the exact layout of the dictionary.
    """

    description: LayoutDescription
    players_config: PlayersConfiguration
    game: GameDescription
    pickup_db: PickupDatabase
    patches: GamePatches
    rng: Random

    cosmetic_patches: CosmeticPatches
    configuration: Configuration

    def __init__(
        self,
        description: LayoutDescription,
        players_config: PlayersConfiguration,
        cosmetic_patches: CosmeticPatches,
    ):
        self.description = description
        self.players_config = players_config
        self.cosmetic_patches = cosmetic_patches

        self.pickup_db = default_database.pickup_database_for_game(self.game_enum())

        self.patches = description.all_patches[players_config.player_index]
        self.configuration = typing.cast(
            "Configuration", description.get_preset(players_config.player_index).configuration
        )
        self.rng = Random(description.get_seed_for_world(players_config.player_index))
        self.game = filtered_database.game_description_for_layout(self.configuration)
        self.memo_data = self.create_memo_data()

    def game_enum(self) -> RandovaniaGame:
        """Returns the game for which this PatchDataFactory is for."""
        raise NotImplementedError

    def create_game_specific_data(self, randovania_meta: PatcherDataMeta) -> dict:
        """Creates the game specific data. Should be overwritten by individual games."""
        raise NotImplementedError

    def create_default_patcher_data_meta(self) -> PatcherDataMeta:
        return {
            "layout_was_user_modified": self.description.user_modified,
            "in_race_setting": not self.description.has_spoiler,
        }

    def create_data(self, custom_metadata: PatcherDataMeta | None = None) -> dict:
        """
        Creates the patcher specific data. Applies custom patcher data on top if they exist.
        :param custom_metadata: If provided, will be used over the default randovania metadata.
        :return: The patcher data, with the randovania metadata included, as a dict.
        """

        randovania_meta = custom_metadata or self.create_default_patcher_data_meta()

        game_data = self.create_game_specific_data(randovania_meta)
        json_delta.patch(game_data, self.patches.custom_patcher_data)
        game_data["_randovania_meta"] = randovania_meta
        return game_data

    def create_memo_data(self) -> dict[str, str]:
        """Used to generate pickup collection messages."""
        return pickup_exporter.GenericAcquiredMemo()

    def create_useless_pickup(self) -> PickupEntry:
        """Used for any location with no PickupEntry assigned to it."""
        return pickup_creator.create_nothing_pickup(self.game.resource_database)

    def create_visual_nothing(self) -> PickupEntry:
        """The model of this pickup replaces the model of all pickups when PickupModelDataSource is ETM"""
        raise NotImplementedError

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

    @classmethod
    def hint_namer_type(cls) -> type[HintNamer]:
        """The type of HintNamer this game uses."""
        raise NotImplementedError

    @classmethod
    def get_hint_namer(
        cls,
        all_patches: dict[int, GamePatches],
        players_config: PlayersConfiguration,
    ) -> HintNamer:
        """Return an instance of this game's HintNamer."""
        return cls.hint_namer_type()(all_patches, players_config)

    @classmethod
    def hint_exporter_type(cls) -> type[HintExporter]:
        """The type of HintExporter this game uses."""
        return HintExporter

    @classmethod
    def get_hint_exporter(
        cls,
        all_patches: dict[int, GamePatches],
        players_config: PlayersConfiguration,
        rng: Random,
        base_joke_hints: list[str],
    ) -> HintExporter:
        """Return an instance of this game's HintExporter."""
        return cls.hint_exporter_type()(
            cls.get_hint_namer(all_patches, players_config),
            rng,
            base_joke_hints,
        )
