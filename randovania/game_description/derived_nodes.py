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
    editor = Editor(game)

    for world, area, node in all_nodes:
        if isinstance(node, DockNode):
            lock_node = DockLockNode.create_from_dock(node)
            # print(f"In {world.name}/{area.name}, create '{lock_node.name}' from '{node.name}'")
            editor.add_node(area, lock_node)


def remove_inactive_layers(game: GameDescription, active_layers: set[str]) -> GameDescription:
    if unknown_layers := active_layers - set(game.layers):
        raise ValueError(f"Unknown layers: {unknown_layers}")

    game = game.get_mutable()
    editor = Editor(game)

    all_nodes = list(game.world_list.all_worlds_areas_nodes)
    for world, area, node in all_nodes:
        if set(node.layers).isdisjoint(active_layers):
            editor.remove_node(area, node)

    return game
