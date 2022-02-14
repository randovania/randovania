from frozendict import frozendict

from randovania.game_description.requirements import ResourceRequirement, RequirementAnd
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo
from randovania.game_description.world.area import Area
from randovania.game_description.world.dock import DockWeakness, DockLockType, DockType
from randovania.game_description.world.node import DockNode
from randovania.game_description.world.node_identifier import NodeIdentifier
from randovania.game_description.world.world import World
from randovania.game_description.world.world_list import WorldList


def test_connections_from_dock_blast_shield(empty_patches):
    # Setup
    req_1 = ResourceRequirement(SimpleResourceInfo("Ev1", "Ev1", ResourceType.EVENT), 1, False)
    req_2 = ResourceRequirement(SimpleResourceInfo("Ev2", "Ev2", ResourceType.EVENT), 1, False)
    dock_type = DockType("Type", "Type", frozendict())
    weak_1 = DockWeakness("Weak 1", DockLockType.FRONT_ALWAYS_BACK_FREE, frozendict(), req_1)
    weak_2 = DockWeakness("Weak 2", DockLockType.FRONT_BLAST_BACK_BLAST, frozendict(), req_2)

    node_1 = DockNode("Node 1", False, None, "", {}, 0,
                      NodeIdentifier.create("W", "Area 2", "Node 2"), dock_type, weak_1)
    node_2 = DockNode("Node 2", False, None, "", {}, 1,
                      NodeIdentifier.create("W", "Area 1", "Node 1"), dock_type, weak_2)

    area_1 = Area("Area 1", None, True, [node_1], {}, {})
    area_2 = Area("Area 2", None, True, [node_2], {}, {})

    world = World("W", [area_1, area_2], {})
    world_list = WorldList([world])

    # Run
    result_1 = list(world_list.connections_from(node_1, empty_patches))
    result_2 = list(world_list.connections_from(node_2, empty_patches))

    # Assert
    assert result_1 == [
        (node_2, RequirementAnd([req_1, req_2])),
    ]
    assert result_2 == [
        (node_1, req_2),
    ]
