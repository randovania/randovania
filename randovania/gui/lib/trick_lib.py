from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo
from randovania.game_description.world_list import WorldList
from randovania.layout.trick_level import LayoutTrickLevel


def difficulties_for_trick(world_list: WorldList, trick: SimpleResourceInfo):
    result = set()

    for area in world_list.all_areas:
        for _, _, requirement in area.all_connections:
            for resource_requirement in requirement.iterate_resource_requirements():
                if resource_requirement.resource == trick:
                    result.add(LayoutTrickLevel.from_number(resource_requirement.amount))

    return result


def used_tricks(world_list: WorldList):
    result = set()

    for area in world_list.all_areas:
        for _, _, requirement in area.all_connections:
            for resource_requirement in requirement.iterate_resource_requirements():
                if resource_requirement.resource.resource_type == ResourceType.TRICK:
                    result.add(resource_requirement.resource)

    return result
