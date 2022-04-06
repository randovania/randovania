from randovania.game_description.editor import Editor
from randovania.game_description.game_description import GameDescription
from randovania.game_description.world.dock_lock_node import DockLockNode
from randovania.game_description.world.dock_node import DockNode


def create_derived_nodes(game: GameDescription):
    """
    Creates any Nodes that are generated of core nodes.
    Currently, creates a DockLockNode for each DockNode.
    :return:
    """
    if not game.mutable:
        raise ValueError("game is not mutable")

    all_nodes = list(game.world_list.all_worlds_areas_nodes)
    last_index = max(n.index for _, _, n in all_nodes) + 1

    editor = Editor(game)

    identifier_by_node = {
        node: game.world_list.identifier_for_node(node)
        for world, area, node in all_nodes
    }

    for world, area, node in all_nodes:
        if isinstance(node, DockNode):
            lock_node = DockLockNode.create_from_dock(node, identifier_by_node[node], index=last_index)
            # print(f"In {world.name}/{area.name}, create '{lock_node.name}' from '{node.name}'")
            last_index += 1
            editor.add_node(area, lock_node)
