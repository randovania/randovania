from typing import Callable, TypeVar

from randovania.game_description.game_description import GameDescription
from randovania.game_description.requirements.base import Requirement
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.resources.trick_resource_info import TrickResourceInfo
from randovania.layout.base.trick_level import LayoutTrickLevel

T = TypeVar("T")


def _process_connections(game: GameDescription, process: Callable[[Requirement, set[T]], None]) -> set[T]:
    result = set()

    for dock_weakness in game.dock_weakness_database.all_weaknesses:
        process(dock_weakness.requirement, result)
        if dock_weakness.lock is not None:
            process(dock_weakness.lock.requirement, result)

    for area in game.world_list.all_areas:
        for _, _, requirement in area.all_connections:
            process(requirement, result)

    return result


def difficulties_for_trick(game: GameDescription, trick: TrickResourceInfo) -> set[LayoutTrickLevel]:
    def process(req: Requirement, result: set[LayoutTrickLevel]):
        for resource_requirement in req.iterate_resource_requirements(game.resource_database):
            if resource_requirement.resource == trick:
                result.add(LayoutTrickLevel.from_number(resource_requirement.amount))

    return _process_connections(game, process)


def used_tricks(game: GameDescription) -> set[TrickResourceInfo]:
    def process(req: Requirement, result: set[TrickResourceInfo]):
        for resource_requirement in req.iterate_resource_requirements(game.resource_database):
            if resource_requirement.resource.resource_type == ResourceType.TRICK:
                result.add(resource_requirement.resource)

    return _process_connections(game, process)
