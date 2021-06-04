from typing import Set, Callable, TypeVar

from randovania.game_description.game_description import GameDescription
from randovania.game_description.requirements import Requirement
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.resources.trick_resource_info import TrickResourceInfo
from randovania.layout.base.trick_level import LayoutTrickLevel

T = TypeVar("T")


def _process_connections(game: GameDescription, process: Callable[[Requirement, Set[T]], None]) -> Set[T]:
    result = set()

    for dock_weaknesses in game.dock_weakness_database:
        for dock_weakness in dock_weaknesses:
            process(dock_weakness.requirement, result)

    for area in game.world_list.all_areas:
        for _, _, requirement in area.all_connections:
            process(requirement, result)

    return result


def difficulties_for_trick(game: GameDescription, trick: TrickResourceInfo) -> Set[LayoutTrickLevel]:
    def process(req: Requirement, result: Set[LayoutTrickLevel]):
        for resource_requirement in req.iterate_resource_requirements(game.resource_database):
            if resource_requirement.resource == trick:
                result.add(LayoutTrickLevel.from_number(resource_requirement.amount))

    return _process_connections(game, process)


def used_tricks(game: GameDescription) -> Set[TrickResourceInfo]:
    def process(req: Requirement, result: Set[TrickResourceInfo]):
        for resource_requirement in req.iterate_resource_requirements(game.resource_database):
            if resource_requirement.resource.resource_type == ResourceType.TRICK:
                result.add(resource_requirement.resource)

    return _process_connections(game, process)
