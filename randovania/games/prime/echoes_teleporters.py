import randovania
from randovania.game_description.area_location import AreaLocation
from randovania.game_description.world_list import WorldList

CUSTOM_NAMES_FOR_ELEVATORS = {
    # Great Temple
    408633584: "Temple Transport Emerald",
    2399252740: "Temple Transport Violet",
    2556480432: "Temple Transport Amber",

    # Temple Grounds to Great Temple
    1345979968: "Sanctuary Quadrant",
    1287880522: "Agon Quadrant",
    2918020398: "Torvus Quadrant",

    # Temple Grounds to Areas
    1660916974: "Agon Gate",
    2889020216: "Torvus Gate",
    3455543403: "Sanctuary Gate",

    # Agon
    1473133138: "Agon Entrance",
    2806956034: "Agon Portal Access",
    3331021649: "Agon Temple Access",

    # Torvus
    1868895730: "Torvus Entrance",
    3479543630: "Torvus Temple Access",
    3205424168: "Lower Torvus Access",

    # Sanctuary
    3528156989: "Sanctuary Entrance",
    900285955: "Sanctuary Spider side",
    3145160350: "Sanctuary Vault side",
}


def elevator_area_name(world_list: WorldList,
                       area_location: AreaLocation,
                       include_world_name: bool,
                       ) -> str:
    if area_location.area_asset_id in randovania.games.prime.echoes_teleporters.CUSTOM_NAMES_FOR_ELEVATORS:
        return randovania.games.prime.echoes_teleporters.CUSTOM_NAMES_FOR_ELEVATORS[area_location.area_asset_id]

    else:
        world = world_list.world_by_area_location(area_location)
        area = world.area_by_asset_id(area_location.area_asset_id)
        if include_world_name:
            return world_list.area_name(area)
        else:
            return area.name
