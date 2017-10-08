from typing import Set

from randovania.resolver.game_description import Node, Area, GameDescription, RequirementList

_gd = None  # type: GameDescription


def _n(node: Node) -> str:
    return "{}/{}".format(_gd.nodes_to_area[node].name, node.name)


def pretty_print_area(area: Area):
    from randovania.resolver.resolver import potential_nodes_from
    print(area.name)
    for node in area.nodes:
        print(">", node.name, type(node))
        for target_node, requirements in potential_nodes_from(node, _gd):
            if target_node is None:
                print("  > None?")
            else:
                print("  >", _n(target_node))
                requirements.pretty_print("      ")
        print()


def debug_print_advance_step(state, reach, requirements_by_node, actions):
    print("Now on", _n(state.node))
    print("Reach:")
    for node in reach:
        print("  > {}".format(_n(node)))
    print("Item alternatives:")
    for node, l in requirements_by_node.items():
        print("  > {}: {}".format(_n(node), l))
    print("Actions:")
    for _action in actions:
        print("  > {} for {}".format(_n(_action), _action.resource))
    print()


_IS_DEBUG = False


def sorted_requirementset_print(new_requirements: Set[RequirementList]):
    to_print = []
    for requirement in new_requirements:
        to_print.append(", ".join(str(item) for item in sorted(requirement.values())))
    print("\n".join(x for x in sorted(to_print)))
