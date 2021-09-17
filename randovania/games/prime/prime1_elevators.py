from randovania.game_description.world.area_location import AreaLocation

# These are hard-coded into the Randomprime API
# Used by the prime1 patcher
RANDOM_PRIME_CUSTOM_NAMES = {
    AreaLocation(3241871825, 2472970646): 'Crater Entry Point',  # 2818083
    AreaLocation(2831049361, 3222157185): 'Phendrana Drifts North\0(Phendrana Shorelines)',  # 45
    AreaLocation(2831049361, 3708487481): 'Phendrana Drifts South\0(Quarantine Cave)',  # 1900634
    AreaLocation(361692695, 3508802073): 'Exterior Docking Hangar',  # 134218592
    AreaLocation(1056449404, 1005235657): 'Magmoor Caverns North\0(Lava Lake)',  # 31
    AreaLocation(1056449404, 3702104715): 'Magmoor Caverns West\0(Monitor Station)',  # 852002
    AreaLocation(1056449404, 1279075404): 'Magmoor Caverns East\0(Twin Fires)',  # 1048608
    AreaLocation(1056449404, 4012840000): 'Magmoor Caverns South\0(Magmoor Workstation, Debris)',  # 1703972
    AreaLocation(1056449404, 3249312307): 'Magmoor Caverns South\0(Magmoor Workstation, Save Station)',  # 1769512
    AreaLocation(2980859237, 1125030300): 'Phazon Mines East\0(Main Quarry)',  # 28
    AreaLocation(2980859237, 3804417848): 'Phazon Mines West\0(Phazon Processing Center)',  # 1638417
    AreaLocation(972217896, 295707720): 'Tallon Overworld North\0(Tallon Canyon)',  # 917509
    AreaLocation(972217896, 597223686): 'Artifact Temple',  # 1049306
    AreaLocation(972217896, 2318493278): 'Tallon Overworld East\0(Frigate Crash Site)',  # 1441848
    AreaLocation(972217896, 366411659): 'Tallon Overworld West\0(Root Cave)',  # 1507378
    AreaLocation(972217896, 212145392): 'Tallon Overworld South\0(Great Tree Hall, Upper)',  # 2687012
    AreaLocation(972217896, 2098226800): 'Tallon Overworld South\0(Great Tree Hall, Lower)',  # 2818083
    AreaLocation(2214002543, 1047210935): 'Chozo Ruins West\0(Main Plaza)',  # 125
    AreaLocation(2214002543, 2199318005): 'Chozo Ruins North\0(Sun Tower)',  # 1572903
    AreaLocation(2214002543, 2784651681): 'Chozo Ruins East\0(Reflecting Pool, Save Station)',  # 4063276
    AreaLocation(2214002543, 594418447): 'Chozo Ruins South\0(Reflecting Pool, Far End)',  # 4128808

    AreaLocation(0x13d79165, 0xb4b41c48): 'Credits',
}

# Names for use when "elevator" isn't implied
UI_CUSTOM_NAMES = {
    # Ruins
    1047210935: "Main Plaza Elevator",
    2199318005: "Sun Tower Elevator",
    2784651681: "Reflecting Pool West Elevator (Save)",
    594418447: "Reflecting Pool South Elevator (Far)",

    # Magmoor
    1005235657: "Lava Lake Elevator",
    3702104715: "Monitor Station Elevator",
    1279075404: "Twin Fires Elevator",
    4012840000: "Magmoor Workstation West Elevator (Debris)",
    3249312307: "Magmoor Workstation South Elevator (Save)",

    # Mines
    1125030300: "Phazon Processing Elevator",
    3804417848: "Main Quarry Elevator",
    
    # Phendrana
    3222157185: "Phendrana Shoreline Elevator",
    3708487481: "Quarantine Cave Elevator",

    # Tallon
    295707720: "Tallon Canyon Elevator",
    2318493278: "Frigate Crash Site Elevator",
    366411659: "Root Cave Elevator",
    212145392: "Lower/North Great Tree Elevator",
    2098226800: "Upper/South Great Tree Elevator"
}

# Names for use when "elevator" is implied
SHORT_UI_CUSTOM_NAMES = {
    # Ruins
    1047210935: "Main Plaza",
    2199318005: "Sun Tower",
    2784651681: "Reflecting Pool West (Save)",
    594418447: "Reflecting Pool South (Far)",

    # Magmoor
    1005235657: "Lava Lake",
    3702104715: "Monitor Station",
    1279075404: "Twin Fires",
    4012840000: "Workstation West (Debris)",
    3249312307: "Workstation South (Save)",

    # Mines
    1125030300: "Phazon Processing",
    3804417848: "Main Quarry",
    
    # Phendrana
    3222157185: "Phendrana Shoreline",
    3708487481: "Quarantine Cave",

    # Tallon
    295707720: "Tallon Canyon",
    2318493278: "Frigate Crash Site",
    366411659: "Root Cave",
    212145392: "Lower/North Great Tree",
    2098226800: "Upper/South Great Tree"
}