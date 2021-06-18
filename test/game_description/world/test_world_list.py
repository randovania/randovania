from randovania.game_description.requirements import ResourceRequirement, RequirementAnd
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo
from randovania.game_description.world.area import Area
from randovania.game_description.world.dock import DockConnection, DockWeakness, DockLockType, DockType
from randovania.game_description.world.node import DockNode
from randovania.game_description.world.world import World
from randovania.game_description.world.world_list import WorldList


def test_connections_from_dock_blast_shield(empty_patches):
    # Setup
    req_1 = ResourceRequirement(SimpleResourceInfo(1, "Ev1", "Ev1", ResourceType.EVENT), 1, False)
    req_2 = ResourceRequirement(SimpleResourceInfo(2, "Ev2", "Ev2", ResourceType.EVENT), 1, False)
    weak_1 = DockWeakness(1, "Weak 1", DockLockType.FRONT_ALWAYS_BACK_FREE, req_1, DockType.DOOR)
    weak_2 = DockWeakness(2, "Weak 2", DockLockType.FRONT_BLAST_BACK_BLAST, req_2, DockType.DOOR)

    node_1 = DockNode("Node 1", False, None, 0, 0, DockConnection(0x30, 0), weak_1)
    node_2 = DockNode("Node 2", False, None, 1, 0, DockConnection(0x20, 0), weak_2)

    area_1 = Area("Area 1", False, 0x20, 0, True, [node_1], {})
    area_2 = Area("Area 2", False, 0x30, 0, True, [node_2], {})

    world = World("World", None, 0x10, [area_1, area_2])
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
