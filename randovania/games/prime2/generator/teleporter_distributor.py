import functools
from random import Random

from randovania.game_description.db.area_identifier import AreaIdentifier
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.game_description.game_database_view import GameDatabaseView
from randovania.game_description.game_patches import TeleporterConnection
from randovania.generator.base_patches_factory import MissingRng
from randovania.generator.teleporter_distributor import get_teleporter_connections
from randovania.layout.lib.teleporters import TeleporterConfiguration, TeleporterShuffleMode


def get_teleporter_connections_echoes(
    teleporters: TeleporterConfiguration, game: GameDatabaseView, rng: Random
) -> TeleporterConnection:
    teleporter_connection: TeleporterConnection = {}

    if not teleporters.is_vanilla:
        if rng is None:
            raise MissingRng("Teleporter")

        if teleporters.mode in {TeleporterShuffleMode.ECHOES_SHUFFLED}:
            connections = elevator_echoes_shuffled(game, rng)
        else:
            connections = get_teleporter_connections(teleporters, game, rng)

        teleporter_connection.update(connections)

    return teleporter_connection


def elevator_echoes_shuffled(game: GameDatabaseView, rng: Random) -> TeleporterConnection:
    from randovania.games.prime2.generator.base_patches_factory import WORLDS

    worlds = list(WORLDS)
    rng.shuffle(worlds)

    result = {}

    @functools.cache
    def area_to_node(identifier: AreaIdentifier) -> NodeIdentifier:
        for _, area, node in game.node_iterator():
            if (
                node.identifier.area_identifier == identifier
                and not node.is_derived_node
                and node.valid_starting_location
            ):
                return node.identifier

        raise KeyError(f"{identifier} has no valid starting location")

    def link_to(source: AreaIdentifier, target: AreaIdentifier) -> None:
        result[area_to_node(source)] = area_to_node(target)
        result[area_to_node(target)] = area_to_node(source)

    def tg_link_to(source: str, target: AreaIdentifier) -> None:
        link_to(AreaIdentifier("Temple Grounds", source), target)

    # TG -> GT
    tg_link_to("Temple Transport A", worlds[0].front)
    tg_link_to("Temple Transport B", worlds[0].left)
    tg_link_to("Temple Transport C", worlds[0].right)

    tg_link_to("Transport to Agon Wastes", worlds[1].front)
    tg_link_to("Transport to Torvus Bog", worlds[2].front)
    tg_link_to("Transport to Sanctuary Fortress", worlds[3].front)

    # inter areas
    link_to(worlds[1].right, worlds[2].left)
    link_to(worlds[2].right, worlds[3].left)
    link_to(worlds[3].right, worlds[1].left)

    return result
