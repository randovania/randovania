from randovania.game_description.world.area_location import AreaLocation
from randovania.game_description.world.world_list import WorldList

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


# Teleporter(0x3bfa3eff, 0xaded752e, 0x9001b): "Temple Transport C",  # 589851
# Teleporter(0x3bfa3eff, 0x62ff94ee, 0x180086): "Transport to Agon Wastes",  # 1572998
# Teleporter(0x3bfa3eff, 0xac32f338, 0x1e000d): "Transport to Torvus Bog",  # 1966093
# Teleporter(0x3bfa3eff, 0x4cc37f4a, 0x200063): "Temple Transport B",  # 2097251
# Teleporter(0x3bfa3eff, 0x87d35ee4, 0x82a008b): "Sky Temple Gateway",  # 136970379
# Teleporter(0x3bfa3eff, 0xcdf7686b, 0x33006e): "Transport to Sanctuary Fortress",  # 3342446
# Teleporter(0x3bfa3eff, 0x503a0640, 0x36001f): "Temple Transport A",  # 3538975
# Teleporter(0x863fcd72, 0x185b40f0, 0x98): "Temple Transport A",  # 152
# Teleporter(0x863fcd72, 0x9860cbb0, 0x6002c): "Temple Transport C",  # 393260
# Teleporter(0x863fcd72, 0x2a01334, 0x38070070): "Main Energy Controller",  # 939982960
# Teleporter(0x863fcd72, 0x2a01334, 0x38070074): "Main Energy Controller",  # 939982964
# Teleporter(0x863fcd72, 0x2a01334, 0x38070075): "Main Energy Controller",  # 939982965
# Teleporter(0x863fcd72, 0x8f01b104, 0x80021): "Temple Transport B",  # 524321
# Teleporter(0x863fcd72, 0x7b4afa6f, 0x9007d): "Sky Temple Energy Controller",  # 589949
# Teleporter(0x42b935e4, 0x57ce3a52, 0x7a): "Transport to Temple Grounds",  # 122
# Teleporter(0x42b935e4, 0xa74ec002, 0x13007b): "Transport to Torvus Bog",  # 1245307
# Teleporter(0x42b935e4, 0x2fc3717, 0x18270061): "Agon Energy Controller",  # 405209185
# Teleporter(0x42b935e4, 0x2fc3717, 0x1827013f): "Agon Energy Controller",  # 405209407
# Teleporter(0x42b935e4, 0x2fc3717, 0x18270143): "Agon Energy Controller",  # 405209411
# Teleporter(0x42b935e4, 0xc68b5b51, 0x2d0073): "Transport to Sanctuary Fortress",  # 2949235
# Teleporter(0x3dfd2249, 0x6f6515f2, 0x81): "Transport to Temple Grounds",  # 129
# Teleporter(0x3dfd2249, 0xcf659f4e, 0x21008a): "Transport to Agon Wastes",  # 2162826
# Teleporter(0x3dfd2249, 0x133bf5b8, 0x142900ad): "Torvus Energy Controller",  # 338231469
# Teleporter(0x3dfd2249, 0x133bf5b8, 0x142900b2): "Torvus Energy Controller",  # 338231474
# Teleporter(0x3dfd2249, 0x133bf5b8, 0x142900b7): "Torvus Energy Controller",  # 338231479
# Teleporter(0x3dfd2249, 0xbf0ee428, 0x450030): "Transport to Sanctuary Fortress",  # 4522032
# Teleporter(0x1baa96c2, 0xd24b673d, 0x26): "Transport to Temple Grounds",  # 38
# Teleporter(0x1baa96c2, 0x35a94603, 0x130094): "Transport to Agon Wastes",  # 1245332
# Teleporter(0x1baa96c2, 0xbb77569e, 0x190087): "Transport to Torvus Bog",  # 1638535
# Teleporter(0x1baa96c2, 0xbaf94a13, 0xc36007c): "Aerie Transport Station",  # 204865660
# Teleporter(0x1baa96c2, 0xd032a6a, 0x83700a1): "Sanctuary Energy Controller",  # 137822369
# Teleporter(0x1baa96c2, 0xd032a6a, 0x83700a8): "Sanctuary Energy Controller",  # 137822376
# Teleporter(0x1baa96c2, 0xd032a6a, 0x8370112): "Sanctuary Energy Controller",  # 137822482
# Teleporter(0x1baa96c2, 0x5d3a0001, 0x41010a): "Aerie",  # 4260106


def elevator_area_name(
        world_list: WorldList,
        area_location: AreaLocation,
        include_world_name: bool,
) -> str:
    if area_location.area_asset_id in CUSTOM_NAMES_FOR_ELEVATORS:
        return CUSTOM_NAMES_FOR_ELEVATORS[area_location.area_asset_id]

    else:
        area = world_list.area_by_area_location(area_location)
        if include_world_name:
            return world_list.area_name(area)
        else:
            return area.name
