from randovania.games.game import RandovaniaGame
from randovania.games.prime import prime1_elevators, echoes_elevators
from randovania.game_description.world.area_location import AreaLocation
from randovania.game_description.world.world_list import WorldList

SHORT_CUSTOM_NAMES_FOR_ELEVATORS = {
    RandovaniaGame.METROID_PRIME: prime1_elevators.SHORT_UI_CUSTOM_NAMES,
    RandovaniaGame.METROID_PRIME_ECHOES: echoes_elevators.CUSTOM_NAMES
}

CUSTOM_NAMES_FOR_ELEVATORS = {
    RandovaniaGame.METROID_PRIME: prime1_elevators.UI_CUSTOM_NAMES,
    RandovaniaGame.METROID_PRIME_ECHOES: echoes_elevators.CUSTOM_NAMES
}

def get_elevator_name_or_default(
    game: RandovaniaGame, 
    asset_id: int, 
    default: str
) -> str:
    return CUSTOM_NAMES_FOR_ELEVATORS.get(game, {}).get(asset_id, default)


def get_elevator_or_area_name(
        game: RandovaniaGame,
        world_list: WorldList,
        area_location: AreaLocation,
        include_world_name: bool
) -> str:
    return _get_elevator_or_area_name(CUSTOM_NAMES_FOR_ELEVATORS, game, world_list, area_location, include_world_name)

def get_short_elevator_or_area_name(
        game: RandovaniaGame,
        world_list: WorldList,
        area_location: AreaLocation,
        include_world_name: bool
) -> str:
    return _get_elevator_or_area_name(SHORT_CUSTOM_NAMES_FOR_ELEVATORS, game, world_list, area_location, include_world_name)

def _get_elevator_or_area_name(
        custom_names_to_use: dict,
        game: RandovaniaGame,
        world_list: WorldList,
        area_location: AreaLocation,
        include_world_name: bool
) -> str:
    custom_names_by_game = custom_names_to_use.get(game, {})

    if area_location.area_asset_id in custom_names_by_game:
        return custom_names_by_game[area_location.area_asset_id]

    else:
        area = world_list.area_by_area_location(area_location)

        if include_world_name:
            return world_list.area_name(area)
        else:
            return area.name
