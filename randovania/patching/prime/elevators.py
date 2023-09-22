from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.game import RandovaniaGame
from randovania.games.prime1.patcher import prime1_elevators
from randovania.games.prime2.patcher import echoes_elevators

if TYPE_CHECKING:
    from randovania.game_description.db.area_identifier import AreaIdentifier
    from randovania.game_description.db.region_list import RegionList

SHORT_CUSTOM_NAMES_FOR_ELEVATORS = {
    RandovaniaGame.METROID_PRIME: prime1_elevators.SHORT_UI_CUSTOM_NAMES,
    RandovaniaGame.METROID_PRIME_ECHOES: echoes_elevators.CUSTOM_NAMES,
}

CUSTOM_NAMES_FOR_ELEVATORS = {
    RandovaniaGame.METROID_PRIME: prime1_elevators.UI_CUSTOM_NAMES,
    RandovaniaGame.METROID_PRIME_ECHOES: echoes_elevators.CUSTOM_NAMES,
}


def get_elevator_name_or_default(game: RandovaniaGame, world_name: str, area_name: str, default: str) -> str:
    return CUSTOM_NAMES_FOR_ELEVATORS.get(game, {}).get((world_name, area_name), default)


def get_elevator_or_area_name(
    game: RandovaniaGame, region_list: RegionList, area_location: AreaIdentifier, include_world_name: bool
) -> str:
    return _get_elevator_or_area_name(CUSTOM_NAMES_FOR_ELEVATORS, game, region_list, area_location, include_world_name)


def get_short_elevator_or_area_name(
    game: RandovaniaGame, region_list: RegionList, area_location: AreaIdentifier, include_world_name: bool
) -> str:
    return _get_elevator_or_area_name(
        SHORT_CUSTOM_NAMES_FOR_ELEVATORS,
        game,
        region_list,
        area_location,
        include_world_name,
    )


def _get_elevator_or_area_name(
    custom_names_to_use: dict[RandovaniaGame, dict[tuple[str, str], str]],
    game: RandovaniaGame,
    region_list: RegionList,
    area_location: AreaIdentifier,
    include_world_name: bool,
) -> str:
    custom_names_by_game = custom_names_to_use.get(game, {})

    area_loc = area_location.as_tuple
    if area_loc in custom_names_by_game:
        return custom_names_by_game[area_loc]

    else:
        area = region_list.area_by_area_location(area_location)

        if include_world_name:
            return region_list.area_name(area)
        else:
            return area.name
