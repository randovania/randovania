from random import Random
from typing import Dict

from randovania.exporter.hints import guaranteed_item_hint
from randovania.exporter.hints.hint_exporter import HintExporter
from randovania.exporter.hints.hint_namer import HintNamer
from randovania.exporter.hints.joke_hints import JOKE_HINTS
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.world.node_identifier import NodeIdentifier
from randovania.game_description.world.logbook_node import LogbookNode
from randovania.game_description.world.world_list import WorldList
from randovania.games.common.prime_family.exporter.hint_namer import colorize_text
from randovania.games.prime2.exporter.hint_namer import EchoesHintNamer
from randovania.games.prime2.patcher import echoes_items
from randovania.interface_common.players_configuration import PlayersConfiguration


def create_simple_logbook_hint(asset_id: int, hint: str) -> dict:
    return {
        "asset_id": asset_id,
        "strings": [hint, "", hint],
    }


def create_patches_hints(all_patches: Dict[int, GamePatches],
                         players_config: PlayersConfiguration,
                         world_list: WorldList,
                         namer: HintNamer,
                         rng: Random,
                         ) -> list:
    exporter = HintExporter(namer, rng, JOKE_HINTS)

    hints_for_asset: dict[NodeIdentifier, str] = {}
    for identifier, hint in all_patches[players_config.player_index].hints.items():
        hints_for_asset[identifier] = exporter.create_message_for_hint(hint, all_patches, players_config, True)

    return [
        create_simple_logbook_hint(
            logbook_node.string_asset_id,
            hints_for_asset.get(world_list.identifier_for_node(logbook_node),
                                "Someone forgot to leave a message."),
        )
        for logbook_node in world_list.iterate_nodes()
        if isinstance(logbook_node, LogbookNode)
    ]


def hide_patches_hints(world_list: WorldList) -> list:
    """
    Creates the string patches entries that changes the Lore scans in the game
    completely useless text.
    :return:
    """

    return [create_simple_logbook_hint(logbook_node.string_asset_id, "Some item was placed somewhere.")
            for logbook_node in world_list.iterate_nodes() if isinstance(logbook_node, LogbookNode)]


_SKY_TEMPLE_KEY_SCAN_ASSETS = [
    0xD97685FE,
    0x32413EFD,
    0xDD8355C3,
    0x3F5F4EBA,
    0xD09D2584,
    0x3BAA9E87,
    0xD468F5B9,
    0x2563AE34,
    0xCAA1C50A,
]


def create_stk_hints(all_patches: Dict[int, GamePatches],
                     players_config: PlayersConfiguration,
                     resource_database: ResourceDatabase,
                     namer: HintNamer,
                     hide_area: bool,
                     ) -> list:
    """
    Creates the string patches entries that changes the Sky Temple Gateway hint scans with hints for where
    the STK actually are.
    :param all_patches:
    :param players_config:
    :param resource_database:
    :param namer:
    :param hide_area: Should the hint include only the world?
    :return:
    """
    resulting_hints = guaranteed_item_hint.create_guaranteed_hints_for_resources(
        all_patches, players_config, namer, hide_area,
        [resource_database.get_item(index) for index in echoes_items.SKY_TEMPLE_KEY_ITEMS],
        True,
    )
    return [
        create_simple_logbook_hint(
            _SKY_TEMPLE_KEY_SCAN_ASSETS[key_number],
            resulting_hints[resource_database.get_item(key_index)],
        )
        for key_number, key_index in enumerate(echoes_items.SKY_TEMPLE_KEY_ITEMS)
    ]


def hide_stk_hints(namer: EchoesHintNamer) -> list:
    """
    Creates the string patches entries that changes the Sky Temple Gateway hint scans with hints for
    completely useless text.
    :return:
    """

    return [
        create_simple_logbook_hint(
            _SKY_TEMPLE_KEY_SCAN_ASSETS[key_number],
            "{} is lost somewhere in Aether.".format(
                colorize_text(namer.color_item, f"Sky Temple Key {key_number + 1}", True)
            ),
        )
        for key_number in range(9)
    ]
