from random import Random

from randovania.game_description.db.area_identifier import AreaIdentifier
from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import ElevatorConnection


def elevator_echoes_shuffled(game_description: GameDescription, rng: Random) -> ElevatorConnection:
    from randovania.games.prime2.generator.base_patches_factory import WORLDS
    worlds = list(WORLDS)
    rng.shuffle(worlds)

    result = {}

    def area_to_node(identifier: AreaIdentifier):
        area = game_description.region_list.area_by_area_location(identifier)
        for node in area.actual_nodes:
            if node.valid_starting_location:
                return node.identifier
        raise KeyError(f"{identifier} has no valid starting location")

    def link_to(source: AreaIdentifier, target: AreaIdentifier):
        result[area_to_node(source)] = area_to_node(target)
        result[area_to_node(target)] = area_to_node(source)

    def tg_link_to(source: str, target: AreaIdentifier):
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
