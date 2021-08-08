# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [Unreleased]

- Fixed: "Open FAQ" in the main window now works correctly.
- Fixed: Pressing Yes to ignore invalid configuration now works correctly. 
- Changed: Randovania now silently handles some invalid configuration states.
- Changed: Improved handling of corrupted repository for old preset versions.

## [3.0.2] - 2021-08-05

- Added: In-game crashes in Metroid Prime now automatically show the error screen.

- Changed: Game Sessions - The window now uses docks for the different parts, meaning you can resize, reorder and even split off.

- Changed: Use different colors for artifact hints in Metroid Prime, for better readability on both scan box and logbook.

- Fixed: Exporting a Metroid Prime ISO with Warp to Start enabled and starting at certain elevator rooms no longer fails.

## [3.0.1] - 2021-08-01

- Changed: Disabled the option to stop exporting a Prime 1 ISO to avoid crashes.

- Fixed: Server will now re-authenticate with Discord, preventing users from logging with the incorrect account.

- Fixed: Game Sessions - History entries with invalid locations no longer cause error messages. 

## [3.0.0] - 2021-07-30

-   **Major** - Metroid Prime 1 is now fully supported, including multiworld and auto tracker!

-   **Major** - Presets are now presented in a tree view, with custom presets being nested under another one. They're also saved separately from Randovania data.

-   **Major** - The auto tracker now have support for different layouts, with their own assets and game support. New themes with icons similar to the game were also added, provided by MaskedKirby.

-   Added: Credits in Metroid Prime 2 now contains a list of where all non-expansions were placed, including possibly other player's for a multiworld. The credits now takes 75 seconds instead of 60 to accomodate this.

-   Added: Button to export the presets used in a game file.

-   Added: Add text description to unusual items in the Item Pool tab.

-   Added: New Help tab with information on how to read the Data Visualizer.

-   Added: In the Map Tracker, it's now possible to right-click a location to see a path from last action to it.

-   Added: A menu option to open the logs folder.

-   Added: The timeout limit is now progressively more forgiving, the more timeouts that happen.

-   Added: Button to set all gates to "Random with Unlocked' for Prime 2.

-   Changed: The items in the starting items popup is now sorted.

-   Changed: Customizing Dark Aether damage is now considered by logic.

-   Changed: Pickup visibility method is now configured in the Item Pool tab.

-   Changed: Multiworld connection is slightly more conservative when giving items.

-   Changed: Updated the Multiworld Nintendont for hopefully more stability.

-   Changed: The session history in multiworld now has different columns for the players involved, pickup and where the pickup was. It's also possible to sort the table by any of these fields.

-   Changed: The ISO prompt dialog now remembers your last used vanilla ISO, for when you delete the internal copy. When opening the file pickers, these start now with the paths from the input fields.

-   Changed: Many Spin/Combo boxes no longer react to the mouse wheel when not focused.

-   Fixed: Closing the dangerous settings warning via the X button is now properly recognized as "don't continue".

-   Fixed: Hint Item Names no longer breaks if you swap games while the table is sorted.

-   Fixed: Hint Item Names now properly list Artifacts and Energy Cells.

-   Fixed: Map Tracker now properly handles unassigned elevators.

-   Fixed: Trick names in the preset are always sorted.

### Metroid Prime 2 - Logic Database Changes

-   **Major** - "Suitless Ingclaw/Ingstorm" trick added to cover traversing rooms with either Ingclaw Vapor or Ingstorm.

#### Added

-   Method of getting over the gate in Mining Station A in reverse with Space Jump and Screw Attack (Expert and above).

-   Method of bypassing the breakable glass in Sand Processing from Main Reactor with Space Jump and Screw Attack (Expert and above).

-   Method of climbing to the top level of Main Gyro Chamber with Space Jump, Screw Attack, and Bombs, and no Scan Visor (Advanced and above).

-   Method of climbing the Sand Processing bomb slot with a Slope Jump for Bombless Bomb Slots (Advanced and above).

-   Method of leaving Dark Agon Temple by opening the gate from OoB with Single Room OoB, Slope Jump, Standable Terrain, Bomb Space Jump, Space Jump, and the Agon Keys (Expert and above).

-   Great Bridge: 
    - Method of reaching Abandoned Worksite door with Space Jump and Extended Dash (Advanced and above).
    - Method of reaching Abandoned Worksite and Torvus Map Station doors from Temple Access Dark door with Boost Ball and Boost Jump (Advanced and above).
    - Method of reaching the pickup with Screw Attack and Single Room Out of Bounds (Expert and above).

-   Method of Crossing Grand Windchamber (both ways) Without Space Jump using Extended Dash (Hypermode).

-   Method of reaching the pickup in Watch Station:
    - With Space Jump, Screw Attack, and Single Room OoB (Expert and above).
    - With only Space Jump and Single Room OoB (Hypermode)

-   Alpha Blogg now has proper requirements for multiple difficulties.

-   Method of Bomb Slots without Bombs in Sanctuary Fortress/Ing Hive - Controller Access/Hive Controller Access without Space Jump (Expert and above).

-   Methods of crossing Torvus Bog - Fortress Transport Access with Gravity Boost or Bombs (No Tricks/Advanced and above).

-   Method of traversing Vault without Space Jump or Screw Attack using Extended Dashes (Advanced and above).

-   Method of reaching Windchamber Gateway item with only Scan Visor using Extended Dashes (Expert and above).

-   Method of reaching Kinetic Orb Cannon in Gathering Hall using Extended Dashes (Expert and above).

-   Method of reaching the pickup in Accursed Lake with a dash (Advanced and above).

-   Method of reaching Temple Security Access from the portal in Aerial Training Site with an Extended Dash (Hypermode).

-   Method of reaching the pickup in Mining Plaza with an Extended Dash (Hypermode).

-   Method of completing the Main Gyro Puzzle with only Space Jump and Screw Attack (Advanced and above).

#### Changed

-   Reaching the pickup in Temple Transport B with a Wall Boost is now Hypermode (from Expert).

-   Reaching the pickup in Path of Roots with only Bombs is now Expert (from Hypermode).

-   Reaching the portal in Hydrodynamo Shaft with Air Underwater and Screw Attack is now Hypermode (from Expert).

-   Reaching the pickup in Dark Torvus Arena with a Roll Jump is now Hypermode (from Expert).

-   Trial Grounds, reaching the door:
    - From the portal with Space Jump and a Slope Jump is now Beginner (from Intermediate).
    - From the left safe zone with a Dash is now Intermediate (from Expert) and without anything is now Advanced (from Expert).
	
-   Opening the Seeker Lock without Seekers in Mine Shaft is now Advanced (From Expert)

-   Opening the Seeker Lock without Seekers in Plain of Dark Worship is now Expert (From Hypermode).

-   Reaching the Windchamber Gateway Door from Windchamber Tunnel with a Boost Jump is now Hypermode (From Expert).

-   Reaching the pickup in Medidation Vista with a Boost Jump is now Expert (From Advanced).

-   Quadraxis and Boost Guardian now have proper health and item requirements with tricks disabled.

-   Activating Controller Access rooms Bomb Slots without Bombs is now Advanced (from Expert).

-   Reaching the Abandoned Worksite/Brooding Ground door from the bridge in Dark/Forgotten Bridge with an Extended Dash is now Hypermode (from Expert).

-   The initial Terminal Fall Abuses in Vault from the scan portal are separate from the final and are now Advanced (from Expert).

-   Catacombs NSJ dash to Transit Tunnel South has been modified to account for Scan Visor, with the original difficulty being raised to Advanced (from Intermediate).

-   Undertemple Shaft NSJ dash from bottom to top of cannon is now Intermediate (from Advanced).

-   Morph Ball is no longer required to reach the portal from the Echo Gate in Profane Path Scan Dash method.

-   Various Standable Terrain tricks (Dark Agon - Portal Site, Temple Grounds - Sacred Path) have been lowered to Beginner/Intermediate (from Advanced). This is to
    attempt to fix an old database limitation from before tricks had their own difficulty levels. 

-   The dashes in Gathering Hall from Transit Tunnel South/West to the Kinetic Orb Cannon are now Intermediate (from Advanced).

-   The Bomb Space Jump NSJ to reach Abandoned Worksite in Great Bridge is now Expert (from Hypermode).

-   The dash to reach the portal in Aerial Training Site from Central Hive Transport West is now Hypermode (from Expert).

-   The dash to leave Hive Temple after Quadraxis via Security Station is now Hypermode (from Expert).

-   The dashes in Command Center (top level) and Accursed Lake without Space Jump are now Beginner (from Intermediate).

-   The dash in Mining Station A to reach Temple Access without Space Jump or Missiles is now Advanced (from Intermediate).

-   The dashes in Trial Grounds to Dark Transit Station without Space Jump are now Advanced (from Intermediate).

-   The dashes in Undertemple Shaft to reach Sacrificial Chamber Tunnel (and back) are now Advanced (from Intermediate). 

-   The dash in Hall of Combat Mastery to reach the upper area after the glass is now Advanced (from Intermediate).

-   Bomb Guardian now has proper logic when shuffling Power Beam.

## [2.6.1] - 2021-05-05

-   Changed: Invalid values for the Multiworld magic item are ignored when detecting if the game is properly connected.
    
-   Fixed: "One-way anywhere" no longer shows up twice in preset warnings for multiworld

-   Fixed: Changing starting location to Ship or Save Stations now works again.

-   Fixed: Torvus Gate elevator is now properly hidden instead of Dark Torvus Ammo Station.

## [2.6.0] - 2021-05-02

-   **Major** - Added: New elevator randomization settings: 
    * New mode: *One-way, elevator room with replacement*. One way elevator, but loops aren't guaranteed.
    * Select which elevators can be randomized.
    * Select possible destinations for *One-way, anywhere*.
    * Randomize Sky Temple Gateway, Sky Temple Energy Controller, Aerie Transport Station and Aerie elevators. *Warning*: These rooms have some details you must consider. Please read the elevators tab for more information.

-   **Major** - Added: The Energy Controllers in Agon Wastes, Torvus Bog and Sanctuary Fortress are always visible in the map, regardless if map is revealed by default. All regions are also always available for selection. This allows the light beam warps after U-Mos 2 to always be used.

-   **Major** - Added: An user preference (in *Customize in-game settings*) for the map to display names of unvisited rooms.
    When randomizing elevators, the elevator rooms are excluded to prevent spoiling their destinations. An option were added to disallow displaying names entirely, since otherwise you can use a Map Station to find the names.  

-   Added: An option to disable the elevator sound effect, preventing it from playing endlessly in certain cases.

-   Added: When a crash happens, the game now displays an error screen instead of just stopping.

-   Added: The *Hint Item Names* tab now supports switching between all 3 Prime games.

-   Added: An option to use an experimental new pickup placement logic, able to place multiple pickups at once.

-   Added: Two additional joke hints. (Thanks CZeke and Geoffistopheles)

-   Added: It's now possible to add Infinite Beam Ammo, Infinite Missiles and Double Damage to the item pool.

-   Added: Player names are now colored yellow in hints.

-   Changed: Elevator names in the tracker uses their customized names, not the vanilla ones.
    
-   Changed: Optimized Randovania startup time and extensive logging of what's being done during it.

-   Changed: Improve scan text for expansions.

-   Changed: Some hints in multiworld games now also include the player names.

-   Changed: Missiles, Power Bombs and Ship Missiles are now only in logic after their respective main launcher, even if it's not required in game. 

-   Changed: You can add up to 99 of any expansion to the pool, up from 64.

-   Fixed: The *Logic damage strictness* multipliers are no longer applied twice.

-   Fixed: *Up to* relative hints are no longer converted into *exactly* if the actual distance matches the displayed number.

-   Fixed: Dark Torvus Bog - Portal Chamber is no longer silently ignored as a starting location.

-   Fixed: Charging your beam to shoot when out of ammo now works even when customizing the ammo type required.

-   Fixed: Having the maximum number allowed of an expansion in a preset no longer causes permalink errors.

-   Fixed: Fixed the game defaulting to Combat Visor after an elevator.

-   Fixed: Multiworld spoiler logs now use 1-indexed player names for locations.

-   Removed: Using Dark Visor as the starting visor is no longer supported. (Game crashes on unmorph for unknown reasons)

### Logic Database Changes

-   Added: Method of reaching the pickup in Hive Gyro Chamber with Space Jump, Boost Ball, and a Boost Jump (Expert and above).

-   Added: Method of climbing Torvus Grove with Space Jump, Screw Attack, and Standable Terrain (Advanced and above).

-   Added: Method of reaching cannon in Great Bridge with Boost Ball and a Boost Jump (Expert and above).

-   Added: Method of reaching the main part of Hall of Combat Mastery with a Scan Dash and after blowing up the glass (Intermediate and above).

-   Added: Method of activating the portal in Portal Terminal with Screw Attack, Slope Jump, and No Bombs or Space Jump (Expert and above).

-   Added: Method of climbing Sacred Bridge with Bombs and a Bomb Space Jump (Advanced and above).

-   Changed: Logic paths that require Screw Attack without Space Jump now make sure to not have Space Jump to be valid.

-   Fixed: Spawn point of Aerie Transport Station is now the door, making DS2 required to take the elevator there.

## [2.5.2] - 2021-02-28

-   Added: The number of items in the pool is now included in the summary.

-   Fixed: Shuffling Combat Visor with item acquisition popups enabled no longer errors.

## [2.5.1] - 2021-02-26

-   Added: Drag and dropping rdvgame and rdvpreset files into the main Randovania window now imports that game file and preset, respectively.

-   Added: Discord bot now posts summary whenever a preset is attached to a message.

## [2.5.0] - 2021-02-19

-   Changed: Preset summary now only include differences from vanilla game.

-   Changed: The relative hint using an item category has been replaced with a relative hint using an area, with up to distance.

### Logic Database Changes

#### Added

-   Method of climbing Sanctuary Temple from the bottom with Bombs and Spider Ball (Intermediate and above).

-   Method of climbing Sanctuary Temple from the bottom with Screw Attack and Single Room Out of Bounds (Expert and above).

-   Method of reaching Worker's Path from the top level in Sanctuary Temple with Scan Visor and an Extended Dash (Expert and above).

-   Method of reaching Windchamber Gateway from Windchamber Tunnel in Grand Windchamber with a Boost Jump (Expert and above).

-   Method of reaching Temple Access in Mining Station A with a Boost Jump (Advanced and above).

-   Method of reaching pickup in Temple Access (Sanctuary) with Space Jump, Screw Attack, and Standable Terrain (Intermediate and above).

-   Method of climbing Temple Access (Sanctuary) with Space Jump, standing on a Rezbit, and dashing off the other Rezbit (Expert and above).

#### Changed

-   Increased weight for Energy Tanks to be selected as progression.

-   Reaching the pickup in Path of Roots from Torvus Lagoon with Gravity Boost, Space Jump, and a Slope Jump is now Intermediate (from Beginner).

-   Reaching the pickup in Grand Windchamber with Space Jump, Screw Attack, Slope Jump, Standable Terrain is now Advanced (from Intermediate).

-   Bomb Jumping over the 2nd light block heading to Hall of Eyes is now Intermediate (from Beginner).

-   Energy Tank requirements for Chykka have been lowered.

#### Fixed

-   Reliquary Grounds now has proper requirements for reaching Ing Reliquary with Light Suit.


## [2.4.2] - 2021-02-08

-   Fixed: Randovania no longer crashes if the connected Dolphin stops emulation.

## [2.4.1] - 2021-02-06

-   Added: Detect if the internal game copy was modified by a future version of Randovania, prompting for the user to press "Delete internal copy".

-   Changed: An error popup now shows up when exporting an ISO fails.

-   Removed: "Automatically track inventory" toggle, as the functionality was already removed.

-   Fixed: Randovania now considers any inventory item with amount above capacity, or capacity above the strict maximum as the game not being connected.

-   Fixed: Error message when the server rejects your client version not being displayed.

-   Fixed: Setting beam ammo expansions to 0 pickups no longer hides the boxes.

## [2.4.0] - 2021-02-01

-   **Major** - Added: The visor and beam you start the game equipped with is now configurable.

-   **Major** - Changed: In multiworld, items are now delivered at the same time as the message. It should also no longer fail to send with Nintendont.

-   Added: Additional joke hints were added.

-   Added: Method to climb to the portal Base Access with just Screw Attack (Intermediate and above).

-   Added: Method to reach the pickup in Grand Windchamber with Space Jump, Screw Attack, and a Slope Jump (Intermediate and above).

-   Added: Method to traverse Ventilation Area B from Bionenergy Production without Bombs by Screw Attacking into the tunnel and destorying the barriers with Missiles (Advanced and above).

-   Added: Method to reach the pickup in Path of Roots from Torvus Lagoon without Morph Ball (Beginner and above).

-   Added: Method to enter the tunnel in Underground Tunnel to Torvus Temple from Torvus Grove with an Instant Morph (Advanced and above).

-   Added: Method to reach the halfpipe pickup in Dark Torvus Arena with Space Jump and a Roll Jump (Expert and above).

-   Added: Method to climb to the upper level in Biostorage Station with Bomb Space Jump (Advanced and above).

-   Added: Method to reach the pickup in Grand Windchamber with a Space Jump, Bomb Space Jump, and a Scan Dash (Expert and above).

-   Added: Method to climb Mining Station B with Space Jump and a Slope Jump (Expert and above).

-   Added: Method to reach the portal in Mining Station B with Space Jump, Scan Visor, and Dashing for Single Room OoB (Expert and above).

-   Added: Method to cross Bitter Well to Phazon Site with Wall Boosts (Hypermode).

-   Added: Method to reach the bomb slot in Training Chamber with Gravity Boost and Air Underwater (Advanced and above).

-   Added: Method to open activate the Bomb Slot in Training Chamber with Darkburst or Sonic Boom (Hypermode).

-   Changed: Auto tracker internally uses a configuration file for the item positions.

-   Changed: The item pool tab when customizing presets now can edit major items directly. 

-   Changed: Defeating Quadraxis with Power Bombs is now Advanced (from Beginner).

-   Changed: Bypassing the statue in Training Chamber from the back with Screw Attack and a Bomb Space Jump is now Expert (from Advanced).

-   Changed: Escaping Hive Temple without Spider Ball is now Expert (from Hypermode).

-   Changed: Bomb Space Jump in Great Bridge/Venomous Pond to reach Abandonded Worksite/Brooding Ground is now Expert (from Hypermode).

-   Changed: Using Seeker Missiles now requires either Combat Visor or Dark Visor.

-   Changed: Bomb Slots without Bombs in Sand Processing, Main Gyro Chamber, and Vault are now Advanced (from Expert).

## [2.3.0] - 2021-01-08

-   Added: Method to enter tunnels in Transit Tunnel East/Undertransit One from Catacombs/Dungeon to Training Chamber/Sacrificial Chamber with an Instant Morph (Intermediate and above).

-   Added: Method to reach the pickup on the Screw Attack wall in Aerial Training Site with a Roll Jump (Expert and above).

-   Added: Method to reach the pickup in Abandoned Worksite from the tunnel with a Boost Jump (Advanced and above).

-   Added: Method to bypass the statue in Training Chamber from the back with Screw Attack and a Bomb Space Jump (Advanced and above).

-   Added: Methods to reach the pickup in Mining Station B with Space Jump, Screw Attack, and Standable Terrain or after the puzzle with a Bomb Jump (Advanced and above).

-   Changed: In multiworld, keybearer hints now tells the player and broad category instead of just player.

-   Changed: Dark Alpha Splinter no longer strictly requires Power Beam.

-   Changed: Crossing Main Gyro Chamber with Screw Attack before stopping the gyro is now Hypermode (from Expert).

-   Changed: Phazon Grounds and Transport to Agon Wastes (Torvus) Seeker Locks without Seekers are now Expert (from Hypermode).

-   Fixed: Properly handle invalid ammo configurations in preset editor. 

-   Fixed: Randovania no longer instantly crashes on macOS.

-   Fixed: Logic properly considers the Transport A gate being gone after entering from that side in Random Elevators.

## [2.2.0] - 2020-12-20

-   Added: 1 HP Mode, where all Energy Tanks and Save Stations leave you at 1 HP instead of fully healing.

-   Added: Added a detailed report of the generator's state when a game fails to generate.

-   Fixed: Generator will no longer ignore players that have no locations left. This would likely cause multiworld generation to fail more often.

-   Fixed: Error messages are properly shown if a game fails to generate.

-   Fixed: Alerts are now properly saved as displayed.

-   Fixed: Errors in the default preset no longer prevent Randovania from starting. 

-   Changed: Optimized game generation, it now takes roughly 2/3 of the time.

-   Changed: Optimized game validation, it now also takes roughly 2/3 of the time.

-   Changed: Relative hints no longer cross portals.

-   Changed: In multiworld, keybearer hints now instead tells the player the item is for, instead of a category.

-   Changed: Decreased the chance of Power Bombs being late in a game.

-   Changed: Account name are updated every time you login via Discord.

-   Changed: Warning about dangerous presets in Multiworld sessions now include the player name.

-   Changed: Roll Jump in Meditation Vista to reach the pickup is now Hypermode (from Expert).

## [2.1.2] - 2020-12-05

-   Added: The Item Pool size now displays a warning if it's above the maximum.

-   Changed: The minimum random starting items is now considered for checking the pool size.

-   Fixed: Being kicked from an online session would leave the window stuck there forever.

-   Fixed: Bulk selecting areas for starting location no longer includes areas that aren't valid starting locations.

## [2.1.1] - 2020-12-02

-   Added: A prompt is now shown asking the user to install the Visual C++ Redistributable if loading the Dolphin backend fails.

-   Fixed: Changing ammo configuration breaks everything.

-   Fixed: Patching ISOs should work again.

-   Fixed: Clean installations can select presets again.

## [2.1.0] - 2020-12-02

-   Changed: Multiworld session history now auto-scrolls to the bottom

-   Changed: The lowest level for a trick is now called "Disabled" instead of "No Tricks".

-   Changed: Minimum Varia Suit Dark Aether is now 0.1, as 0 crashes the game. 

-   Changed: Permalinks are now entirely different for different games.

-   Changed: Preset summary now specifies if hidden model uses ETM or random item.

-   Added: A very basic visualization of the map to the tracker.

-   Added: Trick Details can now be used with all 3 games.

-   Fixed: Changing a trick level to No Tricks no longer cause inconsistent behavior with the permalinks.

-   Removed: Intermediate path for reaching item in Main Reactor from Security Station B door without Screw Attack since it was broken and impossible.
    
-   Changed: Renamed "Before Pickup" to "Next to Pickup" in various locations for more clarity


## [2.0.2] - 2020-11-21

-   Added: Starting locations tab has checkboxes to easily select all locations in an area

-   Added: The map tracker now supports random elevators, translator gates and starting location.

-   Changed: The pickup spoiler in game details is now sorted.

-   Fixed: Multiworld sessions should no longer occasionally duplicate messages.
    
-   Fixed: Custom safe zone healing should now work in multiworld sessions.

-   Fixed: Occasional error with switching an observer into a player.

## [2.0.1] - Skipped

## [2.0.0] - 2020-11-15

This version is dedicated to SpaghettiToastBook, a great member of our community who sadly lost her life this year.

Her contributions to Randovania were invaluable and she'll be missed.

--- 

-   **Major** - New game mode: Multiworld. In this co-op multiplayer mode, there's one different world for each player which is filled with items for specific players.

-   **Major** - Tricks are more organized and can be customized more precisely to a player's desire.

### General

-   Removed: Presets no longer have a global trick level. Each trick is now configured separately.

-   Added: Options for configuring usage of new tricks:
    - Bomb Jump (renamed from Difficult Bomb Jump)
    - Bomb Slot without Bombs
    - Boost Jump
    - Combat
    - Difficult Movement
    - Extended Dash
    - Knowledge
    - Open Gates from Behind
    - Respawn Abuse
    - Screw Attack into Tunnels
    - Seeker Locks without Seekers
    - Single Room Out of Bounds
    - Standable Terrain

-   Changed: The following trick level difficulties were renamed:
    - Trivial -> Beginner
    - Easy -> Intermediate
    - Normal -> Advanced
    - Hard -> Expert
    - Minimal Checking -> Minimal Logic

-   Changed: Replaced Beginner Friendly with Starter Preset, which is now the default preset.

-   Fixed: Energy Tanks can now properly be used as progression.

### Hints

-   Added: Relative hints, where an item is described as being some rooms away from another item or room.

-   Added: Guaranteed hints which tells in which areas (Agon Wastes, Ing Hive, etc) contains the keys for each of your dark temples.
    These hints are placed purely randomly, similarly to the guaranteed Temple Bosses hints.

-   Added: Free hint spots after generation now prefer items from late in progression instead of pure random.

-   Removed: Hints with green item names/joke item names have been removed.

-   Removed: Temple Keys are no longer hinted by progression-based Luminoth lore hints.

-   Changed: All games now have precisely 2 joke hints, which no longer randomly replace a progression hint.

-   Changed: Hints from keybearer corpses now uses a broader category, which leaves unclear if it's an expansion or not.

### GUI

-   Added: An automatic item tracker based on a Dolphin running on the same computer or a special Nintendont build on the same Wifi.

-   Added: A dark theme has been added. It can be toggled in the Advanced menu.

-   Added: Requirements in the logic database can now use templates of requirements, allowing for easy re-use.
    
-   Added: Data Editor can now edit all fields of a node, from type, name and all type specific fields.

-   Added: Data Visualizer and Editor now can operate in the included database for Prime 1 and 3.

-   Added: The Data Editor now displays a warning if you're closing with unsaved changes.

-   Added: Randovania can generate a game by importing permalinks directly from a race on racetime.gg.
    
-   Added: Some tricks now have a description on the Trick Details popup.

-   Fixed: Some complex combination of requirements with different depths now are displayed correctly.

-   Fixed: The Data Visualizer no longer opens behind the Customize Preset window when using the Trick Details popup.

-   Changed: After generating a game, the details shows up in a new window instead of in a new tab.

-   Changed: In game details, the permalink is now placed inside a line edit, so the window doesn't stretch with long permalinks. 

-   Changed: All cosmetic game changes are now configured in the same dialog as the in-game options.

### Quality of Life

-   Added: A button in the Open menu now opens the folder where previously generated games are placed.

-   Added: Charge Beam and Scan Visor now use their respective models in game instead of Energy Transfer Module.

-   Added: The rate of healing for Safe Zones is now configurable.

-   Fixed: Removed Aerie Access and Credits from possible starting locations.

-   Changed: The Mission Final screen now includes the seed hash instead of Permalink, as many permalinks are bigger than the screen.

-   Changed: The elevator scan now includes the world of the connected area.

### Internals/Developer

-   Added: Energy Tanks have doubled weight for the generator.

-   Added: It's now possible to set the default spawn point of an area.

-   Fixed: Fixed solver when an event only connects to a pickup, but that pickup has connections from other nodes.

-   Fixed: The Data Editor no longer errors when saving after creating a new node.

-   Fixed: Certain combinations of item requirements with damage requirements weren't being processed correctly. 

-   Fixed: Duplicated requirements are now properly removed when simplifying requirements.

-   Fixed: Exclude from Room Randomizer is now properly set, restoring many logic paths.

-   Changed: Better error messages when there are references to unknown resources in the database.

-   Changed: The `database` command is no longer a subcommand of `echoes`. It also has the `--game` argument to choose which database to use.

-   Changed: The `_locations_internal` field is no longer needed for .rdvgame files. 

### Logic Database changes

#### Added

-   General:
    - Methods to open all Seeker Missile Doors with Screw Attack (Advanced and above).
    - Method to activate most Bomb Slots without Bombs (Advanced and above).
    - Dark/Light/Annihilator doors and Dark/Light portals require either ammo or Charge Beam.

-   Sanctum, method to fight Emperor Ing without Spider Ball (Hypermode).

-   Transport A Access, method of reaching Temple Transport A door with a Wall Boost (Advanced and above).

-   Abandoned Base, method of reaching portal with Space Jump and Screw Attack (Intermediate and above).

-   Accursed Lake, method of collecting the item and leaving with Morph Ball, Light Suit, Gravity Boost, and Reverse Air Underwater (Advanced and above).

-   Hall of Honored Dead, method of leaving through the Morph tunnel without Space Jump (Expert and above).

-   Industrial Site, method of opening the gate to Hive Access Tunnel from behind with just Charge Beam (Intermediate and above).

-   Ing Windchamber, method of completing the puzzle with Power Bombs instead of Bombs (Beginner and above).

-   Landing Site, method of reaching Service Access door:
    - With Bombs and Screw Attack (Intermediate and above).
    - With Space Jump and Bomb Space Jump (Intermediate and above).

-   Meeting Grounds, method of reaching the tunnel with Space Jump and a Bomb Space Jump (Intermediate and above).

-   Temple Assembly Site:
    - Methods of reaching Dynamo Chamber door with a Bomb Jump (Beginner and above), a Dash (Intermediate and above), or a Roll Jump (Advanced and above).
    - Methods of reaching the portal without moving the light block with Single Room Out of Bounds and either Screw Attack or Space Jump (Expert and above).
    - Method of leaving from the portal with Single Room Out of Bounds and Screw Attack (Expert and above).

-   Windchamber Gateway:
    - Method of reaching the item with a Boost Jump (Advanced and above) and returning with an Extended Dash (Expert and above).
    - Method of reaching Path of Eyes door from Grand Windchamber door with an Extended Dash (Advanced and above).

-   Bioenergy Production, method to reach Storage C door or item from top level with Extended Dash (Expert and above).

-   Central Station Access/Warrior's Walk, method of climbing the ledge with an Instant Unmorph Jump (Hypermode).

-   Crossroads, method to reach the item from the half pipe with just Screw Attack (Advanced and above).

-   Dark Transit Station, method to reach the ledge from Duelling Range with a Bomb Jump (Beginner and above).

-   Portal Access, method of crossing to Judgement Pit using Screw Attack without Z-Axis (Beginner and above).

-   Doomed Entry, method to climb room with Space Jump and Screw Attack (Beginner and above).

-   Feeding Pit:
    - Method of reaching Ing Cache 1 door with Space Jump and Screw Attack (No Tricks and above).
    - Method of climbing to Watering Hole door without any items (Expert and above).
    - Method of escaping the pool using Light Suit and a Bomb Space Jump no Space Jump or Gravity Boost (Hypermode)

-   Main Reactor, method of reaching Dark Samus 1 fight from Ventilation Area A door with Space Jump, Bombs, and a Bomb Space Jump (Intermediate and above).

-   Mining Station B:
    - Method to climb to the Seeker door without Morph Ball and with Space Jump (Beginner and above).
    - Method to reach the portal without breaking the rock with Single Room Out of Bounds and Screw Attack (Expert and above).

-   Sandcanyon, method to reach the item with Space Jump and Single Room Out of Bounds (Expert and above).

-   Transport Center/Crossroads, method to climb the halfpipe with Space Jump (Advanced and above).

-   Abandoned Worksite:
    - Method of reaching the item with a Bomb Space Jump without Space Jump (Advanced and above).
    - Method of reaching the tunnel from Forgotten Bridge with a Slope Jump (Intermediate and above).

-   Catacombs:
    - Method to reach the Bomb Slot with Air Underwater and Screw Attack (Advanced and above).
    - Method to reach Transit Tunnel East with a Combat/Scan Dash (Advanced and above).
    - Method to reach the portal with Screw Attack (Intermediate and above).
    - Method to reach Transit Tunnel East/South with Morph Ball, Gravity Boost, and Reverse Air Underwater (Advanced and above).
    - Method to reach Transit Tunnel South with Jump Off Enemy (Advanced and above).

-   Dark Arena Tunnel, method of reaching either door with Screw Attack and Single Room Out of Bounds (Advanced and above).

-   Dark Forgotten Bridge:
    - Method to perform the gate clip to Dark Falls/Dark Arena Tunnel with a Ledge Clip Jump (Hypermode).
    - Method to reach Bridge Center from Putrid Alcove door with only Scan Visor (Advanced and above).
    - Method to reach Brooding Ground door from the bridge before rotating and with an Extended Dash (Expert and above).

-   Forgotten Bridge:
    - Method to reach Abandoned Worksite door from the bridge before rotating and with an Extended Dash (Expert and above).
    - Method to reach Bridge Center with Morph Ball, Gravity Boost, and Reverse Air Underwater (Advanced and above).

-   Gathering Hall: 
    - Method to reach the Kinetic Orb Cannon with Gravity Boost and Bombs (Expert and above) or Gravity Boost and Space Jump (Beginner and above).
    - Method to reach Transit Tunnel South from Transit Tunnel West with Morph Ball, Gravity Boost, and Reverse Air Underwater (Advanced and above).
    - Method to reach the Spider Ball tracks with Morph Ball, Gravity Boost, and Reverse Air Underwater (Advanced and above).
    - Methods to escape the halfpipe after draining the water with Space Jump and Bomb Space Jump or Space Jump and Screw Attack (Advanced and above).

-   Great Bridge, method of reaching the lower Temple Access door from Path of Roots door with Screw Attack and Slope Jump (Intermediate and above).

-   Main Hydrochamber/Hydrodynamo Station, methods to climb rooms without Gravity Boost and with Air Underwater (Advanced and above), Space Jump, and Screw Attack (Hypermode).

-   Meditation Vista, methods of reaching the item with a Boost Jump (Advanced and above), Roll Jump (Expert and above), or Extended Dash (Hypermode).

-   Path of Roots, method of reaching the item using:
    - Morph Ball, Bombs and Space Jump (Advanced and above).
    - Morph Ball, Gravity Boost, and Reverse Air Underwater (Advanced and above).
    - Morph Ball, Bombs, and Standable Terrain (Hypermode).

-   Plaza Access, method of reaching the doors and the item with Screw Attack and Single Room Out of Bounds (Advanced and above).

-   Portal Chamber (Light World), method of reaching the portal from Torvus Lagoon door with Screw Attack and Single Room Out of Bounds (Advanced and above).

-   Putrid Alcove, method of getting the item and leaving without any items (Expert and above).

-   Sacrificial Chamber, method of crossing gap to Sacrificial Chamber Tunnel with Extended Dash (Expert and above).

-   Torvus Grove, method of climbing the room without Boost Ball (Expert and above).

-   Torvus Plaza:
    - Method of getting the item without Boost Ball and/or Spider Ball (Advanced and above).
    - Method of leaving the room with Space Jump and Bombs (Advanced and above).

-   Torvus Temple, method of reaching the pirate fight from the lower level with Screw Attack and Single Room Out of Bounds (Advanced and above).

-   Training Chamber:
    - Method to exit the spinner with Power Bombs instead of Bombs (Beginner and above).
    - Method to climb to the top of the statue with Gravity Boost and Bombs (Intermediate and above).
    - Method to climb to the top of the statue with Space Jump, Scan Dash, and Underwater Dash (Advanced and above).
    - Method to climb to the top of the statue with Space Jump and Extended Dash (Expert and Above).

-   Underground Tunnel, method to access Torvus Temple from Torvus Grove with Screw Attack (Expert and above).

-   Undertemple, method to have PB Guardian break PB door using bombs (Advanced and above).

-   Undertemple Access, method of reaching the item using Screw Attack and Jump Off Enemy (Hypermode).

-   Venomous Pond, method to reach the key from the Save Station with Screw Attack and Standable Terrain (Beginner and above).

-   Aerial Training Site, methods to cross the room from various nodes with Dashes, Roll Jumps, and Extended Dashes (Intermediate/Expert and above).

-   Aerie, method of collecting the item:
    - Without entering the Dark World (Expert and above).
    - With only Screw Attack (Beginner and above).

-   Dynamo Access, method to cross over the Spider Track with Space Jump and Standable Terrain (Beginner and above).

-   Dynamo Works:
    - Method of collecting the item with a Roll Jump and Instant Morph (Expert and above).
    - Method of reaching the upper door with a Bomb Space Jump (Beginnner and above).

-   Grand Abyss, methods of crossing the gap with Boost Jump (Advanced and above) or Extended Dash (Expert and above).

-   Hall of Combat Mastery:
    - Method of collecting the item with a Wall Boost (Expert and above).
    - Methods of reaching the item, and skipping the Spider Track to and from Central Area Transport East with Screw Attack (Intermediate and above).

-   Hive Entrance, method of reaching the Flying Ing Cache with Screw Attack and Single Room Out of Bounds (Hypermode).

-   Hive Dynamo Works:
    - Method of collecting the Flying Ing Cache item and leaving with Space Jump and Scan Visor (Advanced and above).
    - Method of reaching the Flying Ing Cache from portal side and vice versa with Screw Attack and Single Room Out of Bounds (Expert and above).

-   Hive Summit, method of reaching the portal:
    - With Space Jump and Standable Terrain (Intermediate and above).
    - With Space Jump, Boost Ball, Boost Jump, and Out of Bounds (Expert and above).

-   Hive Temple:
    - Method of fighting Quadraxis with Power Bombs instead of Bombs (Beginner and above).
    - Methods of leaving the room without Spider Ball after Quadraxis with Boost Ball or Space Jump (Hypermode).

-   Judgment Drop, method of reaching the portal with Space Jump and Single Room Out of Bounds (Expert and above).

-   Main Research, method of fighting Caretaker Drone without Bombs (Expert and above).

-   Reactor Core, method of reaching the item with only Space Jump (Expert and above).

-   Sanctuary Entrance, method to reach the cannon to the item with only Morph Ball, Spider Ball, and Power Bombs (Advanced and above).

-   Vault Attack Portal, method to cross either direction with just Screw Attack (Expert and above).

-   Watch Station, method of accessing the Spider Ball track to Watch Station Access door and Sentinel's Path door and back with an Instant Morph (Intermediate and above).

-   Watch Station Access, methods to cross the pit in either direction using:
    - Boost Ball and Boost Jump (Advanced and above).
    - Space Jump, Scan Visor, and Scan Dash (Advanced and above).

-   Workers Path, method of crossing the room from Sanctuary Temple with a Boost Jump (Advanced and above).

#### Fixed

-   Scan Visor Requirements: 
    - Dash Requirements in many rooms
    - Grand Abyss Bridge terminal
    - Sand Processing item
    - Staging Area terminal
    - Torvus Lagoon terminal
    - Trooper Security Station Event coming from Communication Area
    - Various Dash Requirements

-   Dark Aether Damage Requirements have been added to every room in the Dark World.

-   Morph Ball requirements added to Morph Ball Doors and various rooms.

-   Invisible Objects and Dark Visor Requirements:
    - Screw Attack without Space Jump in Unseen Way (Intermediate and above)
    - Screw Attack without Space Jump in Phazon Grounds (Advanced and above)

-   Entrance to Agon Map Station now requires Bombs, Power Bombs, or Boost Ball if coming from either direction, or Screw Attack and Space Jump as well if coming from Mining Plaza.

-   Added Charge Beam and Beam Ammo Requirements to Profane Path and Sentinel's Path.

-   Sand Processing:
    - Now requires items to climb the room before draining the sand: Space Jump, with a Bomb Jump (Beginner and above) or with Screw Attack (Intermediate and above)
    - Screw Attacking into the tunnel is now Expert (from Hypermode).

-   Portal Site:
    - Now does not require the gate open to enter from Portal Access.
    - Now does not require the gate closed to enter from Crossroads.

-   Service Access now properly includes Wall Boost to Meeting Grounds from Landing Site on Advanced.

#### Changed

-   Many nodes with missing requirements have been updated/cleaned up.

-   Simplified nodes in many rooms for ease of logic navigation.

-   Various tricks have been changed to more accurately represent the required method.

-   Abandoned Base, Bomb Jump to transport is now Advanced (from Intermediate).

-   Accursed Lake, Dash to Safe Zone from Flying Ing Cache is now Intermediate (from Beginner).

-   Communication Area:
    - Standable Terrain to reach the item is now Beginner (from Intermediate).
    - Screw Attack without Space Jump to reach Storage Cavern A is now Beginner (from Intermediate).
    - Double Bomb Jump up Standable Terrain is now Intermediate (from Advanced).

-   GFMC Compound, Extended Dash to reach the item on the Ship without Space Jump is now Expert (from Hypermode).

-   Grand Windchamber, reaching the pickup with Terminal Fall Abuse after solving the Ing Windchamber puzzle is now Beginner (from Intermediate).

-   Path of Eyes, Bomb Jumps to get over Light blocks are now Beginner (from Intermediate).

-   Service Access, crossing upper tunnel without Boost Ball is now Advanced (from Intermediate).

-   Temple Assembly Site, method to reach the item with Screw Attack is now Beginner (from Intermediate).

-   Agon Temple, Slope Jumps to skip the fight barriers are now Beginner (from Advanced).

-   Battleground, climbing to top safe zone via Standable Terrain is now Beginner (from Intermediate).

-   Central Mining Station, Scan Dash to upper level from Central Station Access is now Expert (from Advanced).

-   Command Center Access, exiting tunnel without Space Jump is now Beginner (from Intermediate).

-   Doomed Entry, Slope Jump to reach the upper level from the portal is now Beginner (from Intermediate).

-   Double Path, crossing lower path without Space Jump is now Beginner (from Intermediate).

-   Feeding Pit, method to climb to Watering Hole with just Screw Attack is now Beginner (from Intermediate).

-   Mining Plaza, climbing the room with Screw Attack is now Beginner (from Intermediate).

-   Mining Station A, reaching Front of Lore Scan from Room Center with a Bomb Jump is now Intermediate (from Advanced).

-   Mining Station B:
    - Reaching Transit Station door from room center with Screw Attack after opening the portal is now Intermediate (from Hypermode).
    - Reaching the bomb slot to open the portal with Standable Terrain and Screw Attack is now Intermediate (from Advanced).
    - Reaching the bomb slot to open the portal with Slope Jump and Space Jump is now Advanced (from Expert).

-   Portal Access, returning from Judgment Pit without Space Jump is now Beginner (from Intermediate).

-   Trial Grounds, Standable Terrain to reach the door from the portal is now Beginner (from Intermediate).

-   Catacombs, reaching the portal with Morph Ball and Reverse Air Underwater is now Advanced (from Expert).

-   Crypt, Bomb Jump to Laser Platfrom from bottom Safe Zone is now Beginner (from Intermediate).

-   Forgotten Bridge, reaching Bridge Center with Bombs and Screw Attack is now Intermediate (from Advanced).

-   Gathering Hall:
    - Reaching Transit Tunnel South/West Doors from top door with Morph Ball and Roll Jump is now Expert (from Advanced).
    - Reaching Transit Tunnel East with Spider Ball and Boost Ball is now Beginner (from Intermediate).

-   Great Bridge:
    - Slope Jumps to reach Map Station from Bottom Level and from Map Station to Upper Level are now Beginner and Intermediate (from Intermediate and Advanced, respectively).
    - Bomb Space Jump with Space Jump to reach the Translator Gate is now Advanced (from Expert).

-   Poisoned Bog, reaching Portal Chamber door with just Screw Attack is now Advanced (from Intermediate).

-   Torvus Lagoon, reaching Portal Chamber from Temple Transport Access is now Intermediate (from Advanced).

-   Training Chamber, Standable Terrain to reach Fortress Transport Access from Top of Statue and back is now Beginner (from Intermediate).

-   Venomous Pond, reaching the key from the Save Station with Screw Attack is now Beginner (from Intermediate).

-   Aerial Training Site, Screw Attack at Z-Axis from Central Hive Area West door to the portal or Temple Security Access door is now Intermediate (from Advanced).

-   Dynamo Access, crossing over the Spider Track with a Slope Jump is now Beginner (from Intermediate).

-   Hall of Combat Mastery, Instant Morph tricks to the item and Central Area Transport East and back are now Advanced (from Intermediate).

-   Hive Dynamo Access, opening Echo Gate from behind is now Beginner (from Intermediate).

-   Hive Dynamo Works:
    - Reaching the Seeker Lock Safe Zone from Hive Dynamo Access door with Terminal Fall Abuse is now Beginner (from Intermediate).
    - Reaching the Flying Ing Cache from the tunnel with Screw Attack is now Beginner (from Intermediate).
    - Reaching the Flying Ing Cache from the tunnel and back with Standable Terrain is now Intermediate (from Advanced).
    - Opening the Seeker Lock from behind is now Beginner (from Intermediate).

-   Hive Summit, Standable Terrain to reach portal inside glass area is now Beginner (from Intermediate).

-   Hive/Temple Access, reaching the upper door with Screw Attack at Z-Axis is now Beginenr (from Intermediate).

-   Transit Station, reaching the top portal with Screw Attack is now Beginner (from Intermediate).

-   Vault:
    - Terminal Fall abuse to reach Grand Abyss door from bridge portal with Space Jump is now Beginner (from Intermediate).
    - Reaching the Bomb Slot with Screw Attack from the bridge portal is now Beginner (from Intermediate).

-   Watch Station, Screw Attack at Z-Axis from Watch Station door to Sentinel's Path door is now Beginner (from Intermediate).

-   Watch Station Access, reaching the Watch Station door from the pickup with just Screw Attack is now Beginner (from Intermediate).

## [1.2.2] - 2020-06-06

-   Changed: Re-organized the tabs in the preset customization window

-   Changed: The reset map tracker menu action is now visible on non-windows platforms.

-   Fixed: Exporting ISOs with Menu Mod should now work on macOS.

## [1.2.1] - 2020-05-30

-   Added: Randovania releases now includes a packages for macOS.

## [1.2.0] - 2020-05-25

-   *Major* - Added: The text of the scan that unlocks an elevator now includes the
    elevators destination.
    
-   *Major* - Added: Translator gates can be configured as Unlocked: the hologram will be invisible and can be scanned
    without any translator.

-   *Major* - Added: The default in-game options can now be configured from Randovania.

-   *Major* - Added: How much ammo each beam uses to shoot uncharged, charged and charge combos is now configurable,
    along with the ammo it uses.

-   *Major* - Changed: The database now uses a new format which allows for any combination of "Or"/"And" statements.
    The Data Visualizer and Editor were both updated to take advantage of this.

-   Added: An option to connect Sky Temple Gateway directly to the credits, skipping the final bosses.

-   Added: How much energy you get for each Energy Tank is now configurable.

-   Added: The in-game Hint System has been removed. The option for it remains, but does nothing.

-   Changed: The spoiler log now lists the order in which items where placed, with their location and hints,
    instead of a detailed playthrough for completion.

-   Changed: The logbook entries that contains hints are now named after the room they're in, with the categories
    being about which kind of hint they are.
    KNOWN ISSUE: While scanning something, the categories that show up are incorrect.

-   Added: Open -> Trick Details menu entry, similar to what's available in the
    Trick Level tab when customizing a preset. 
    
-   Added: Play -> Import game file, to load spoiler logs.

-   Added: The "Heals?" checkbox in the database editor now works.

-   Added: The permalink import dialog now shows an error message for invalid permalinks.

-   Changed: One-way elevators now have a chance of warping to credits.

-   Changed: Clarified that the item from Space Jump Guardian and Power Bomb Guardian
    must be collected for the appropriate events to be triggered. 
    
-   Changed: In Menu Mod, the list of rooms to warp to is now sorted.

-   Changed: The export-areas command line option now outputs details about requirements for each area.

-   Internal: A human-readable copy of the database is now kept next to the database file, for easier diffs.

-   Fixed: Debug logs can no longer be enabled for non-spoiler permalinks.

-   Added: Missile Expansions have a 1/8192 chance of using Dark Missile Trooper model.

-   Fixed: Progress bar no longer goes to an indefinite status when generation fails.

-   Added: Checkbox for automatically exporting a spoiler log next to the ISO.

-   Fixed: Only the last digit of the game id is changed, instead of the full game id.

### Logic Database changes

-   Fixed: Staging Area is now correctly considered a dark world room.

-   Fixed: The Ing Cache in Dark Oasis now requires Power Bombs. 

-   Fixed: Bioenergy Production correctly requires Scan Visor for connections using the racks.

-   Added: In Bioenergy Production, method of reaching the Storage C door with Space Jump and Screw Attack (Easy and above)

-   Added: In Bioenergy Production, method of reaching the Storage C door using a roll jump (Normal and above).

-   Added: In Bioenergy Production, method of reaching the Ventilation Area B door using Screw Attack without Space Jump (Normal and above).

-   Added: In Bioenergy Production, additional upper level connections using Space Jump and Screw Attack.

-   Added: In Sandcanyon, method of reaching the center platform using a roll jump and boost ball (Hard and above).

-   Changed: In Command Center Access, the wall boosts to reach the lower Central Mining Station and Command Center doors from the morph ball tunnel are now Normal difficulty (from Hard).

-   Changed: In Portal Chamber (both light and dark Torvus) , all wall boosts are now Normal difficulty (from Hard).

-   Changed: In Undertransit Two, all wall boosts are now Easy difficulty (from Hard).

-   Changed: In Temple Security Access, all wall boosts are now Normal difficulty (from Hard).

-   Changed: In Watch Station, all wall boosts are now Normal difficulty (from Hard).

-   Added: In Watch Station, a wall boost method of reaching the Watch Station Access door from the Sentinel's Path door using Spider Ball and Boost Ball (Normal and above).

-   Changed: In Service Access, methods using a wall boost to reach the Meeting Grounds door from the upper Morph Ball tunnel are now Normal difficulty (from Hard).

-   Changed: In Great Bridge, the wall boost to reach the lower Temple Access Door from the Path of Roots door is now Easy difficulty (from Hard).

-   Changed: In Transit Tunnel East, the wall boost to reach the Training Chamber door from the Catacombs door is now Easy dififculty (from Hard).

-   Changed: In Transit Tunnel South, all wall boosts are now Easy difficulty (from Hard).

-   Added: In Hall of Honored Dead, a method of obtaining the item with Power Bombs (Trivial and above).

-   Added: Many Light Ammo/Dark Ammo/Morph Ball/Charge Beam requirements.

-   Added: In Bioenergy Production, methods of reaching the item and the door to Ventilation Area B using a Bomb Space Jump and Screw Attack without Space Jump (Hypermode).

-   Fixed: Biostorage Station now requires Space Jump or Scan Visor to reach the upper level (No Tricks and above).

-   Changed: In Sand Processing, the method of reaching the item without Boost Ball requires the Bomb Space Jump trick, and no longer requires Screw Attack.

-   Added: In GFMC Compound, a method of reaching the ship item with Screw Attack (Normal and above).

-   Added: In Main Gyro Chamber, a method of reaching the bottom of the gyro area from the middle of the room with Screw Attack (Easy and above).

-   Changed: In Workers Path, Morph Ball Bomb is no longer required.

-   Changed: In Main Reactor, unlocking the gate no longer requires Space Jump, and is now Trivial difficulty (from Easy).

-   Added: In Landing Site, a method of reaching the door to Service Access using Morph Ball Bomb and a Slope Jump (Normal and above).

-   Added: Methods of climbing Central Station Access and Warrior's Walk using Screw Attack (Hard and above) and a wall boost (Hypermode).

-   Added: A method of opening the echo gate in Hive Dynamo Access from the Hive Gyro chamber side using Sonic Boom or Darkburst (Easy and above).

-   Changed: In Reliquary Grounds, the method of reaching the door to Ing Reliquary using Screw Attack is now Normal difficulty (from Hard).

-   Added: In Reliquary Grounds, a method of reaching the door to Ing Reliquary using Morph Ball Bomb and Screw Attack without Space Jump (Easy and above).

-   Added: In Phazon Pit, a method of reaching the door to Phazon Grounds using a roll jump and boost ball (Hard and above).

-   Changed: Climbing Hall of Stairs with Space Jump is now Trivial difficulty (from Easy).

-   Added: In Transport Center, a method of reaching the elevator door from the portal using Screw Attack without Space Jump (Trivial and above).

-   Added: In Mining Station A, a method to reach the Temple Access door using Screw Attack (Trivial and above).

-   Added: In Gathering Hall, a method to reach the Transit Tunnel South from the Gathering Access door using Space Jump (Easy and above).

-   Added: In Industrial Site, a method of opening the Industrial Site gate from the wrong side using a missile (Trivial and above).

-   Fixed: Removing the Aerial Training Site barrier requires Scan Visor.



## [1.1.1] - 2020-03-11

-   Added: The preset summary now includes if menu mod is enabled.

-   Fixed: The cursor no longer snaps to the end on all changes, in the permalink
    input field.

-   Fixed: "Starting Items" is now properly implemented in the preset summary.
    
-   Changed: "Custom Items" is now "Item Pool" in the preset summary, and lists all
    deviations from the standard item pool.

## [1.1.0] - 2020-03-10

-   Added: The pickup notice for a locked expansion is more clear of what's going on.

-   Added: The "Save ISO" dialog now remembers the last output directory used.

-   Added: A copy of the game file is automatically saved to 
    `%LOCALAPPDATA%\Randovania\game_history` whenever a game is generated. There's no
    interface in Randovania to view this history.

-   Changed: The "Save Spoiler" button now provides a default name for the game file. 

-   Changed: Shortened permalinks with customized starting locations.

-   Changed: Preset are now exported to `.rdvpreset` files, to avoid Discord truncating the
    file names.

-   Fixed: When changing a preset name, the cursor no longer moves to end after any change.

### Logic Database changes

-   Fixed: The pickup in Undertransit One now requires Power Bombs, to avoid soft locks.

-   Fixed: The second Portal Chamber is now correctly considered a Dark Torvus Bog room.

## [1.0.0] - 2020-02-09

-   *Major* - Added: Support for multiple presets of options, as well as saving your own presets.

-   *Major* - Changed: The user experience for creating a new game has been changed completely.

-   Added: Three new methods of shuffling elevators: *Two-way, unchecked*, *One-way, elevator room*
    and *One-way, anywhere*. The elevators tab has more details of how these work.

-   Added: Add a setting for how strict the damage requirements are.

-   Added: It's now possible to exclude locations from having any progression on them.

-   Added: You can choose an arbitrary number of locations to choose randomly from for starting location.

-   Changed: A Luminoth Lore scan is less likely to have hints for what was already accessible
    when that scan was found.
    
-   Changed: Power Bombs and Progressive Grapple are now slightly more likely to appear earlier.
    
-   Changed: The hints randomly assigned at the end of generation are less likely to be repeats.

-   Changed: Loading a new game will automatically clear any existing one.

-   Changed: Minimal Checking now also checks of Dark Agon Temple Keys and Dark Torvus Temple Keys.

-   Removed: The Progressive Launcher has been removed.

-   Removed: The settings for fixing the translator gates have been removed for now, to be re-added
    on a future "Advanced" tab.

-   Removed: The create-permalink command line argument has been removed.

### Logic Database changes

-   Fixed: Spider Guardian fight now requires Dynamo Works Quads Gone to be triggered.

-   Fixed: Boost Guardian now properly requires Bombs.

-   Added: Escaping Dark Torvus Arena with a BSJ, for Normal. (See #581).

-   Added: Activating the Industrial Site gate backwards, using charged Annihilator Beam, for Trivial. (See #582).

## [0.29.1] - 2019-10-01

-   Fixed: Fix AttributeError preventing major/minor randomization from working.

-   Fixed: Seeds where no progression is needed to finish should no longer fail to generate. 

## [0.29.0] - 2019-10-01

-   *Major* - There is now an option for a major/minor split randomization mode, in which expansions and
    non-expansion items are shuffled separately.

-   *Major* - Changed: Item hints and Sky Temple Key hints now distinguish between the light and dark worlds.
    For example, the room in which Quadraxis resides will be shown as "Ing Hive - Hive Temple" rather than
    "Sanctuary Fortress - Hive Temple".

-   *Major* - Added: the "Invisible Objects" trick in places where a visor would otherwise be used to be able to see
    something (such as an invisible platform).

-   *Major* - Added: Title screen now shows a three-word representation of the seed hash.

-   Added: As an experimental feature, it is now possible to shuffle Power Beam, Charge Beam, Scan Visor and Morph Ball.
    These items use Energy Transfer Module model in game.

-   Added: You can now place a pickup that temporarily gives Cannon Ball when collected. It uses Boost Ball's model.

-   Changed: Some item categories were given clearer names:
    - Dark Agon Keys, Dark Torvus Keys, and Ing Hive Keys are now referred to as "red Temple Keys" instead of
    "Temple Keys".
    - Items that aren't keys or expansions are collectively referred to as "major upgrades" instead of "major items".
    - Red Temple Keys and Sky Temple Keys are now collectively referred to as "Dark Temple Keys" instead of "keys".

-   Fixed: "Beam combos" are now called "charge combos".

-   Changed: The hints acquired from keybearer corpses now clarify that the item is the one contained in a Flying
    Ing Cache.

-   Changed: Each hint for the items guarded by Amorbis, Chykka, and Quadraxis now contains the corresponding
    Guardian's name.

-   Changed: The hint for the vanilla Light Suit location now has special text.

-   Changed: Item names in hints are now colored orange instead of red.

-   Changed: Some hints were added, some removed, and some modified.

-   Changed: Item scans were slightly edited.

-   Changed: The Sky Temple Key hints no longer use ordinal numbers.

-   Added: The seed hash is shown in Randovania's GUI after patching is done.

-   Changed: Generation will now be retried more times before giving up.

-   Changed: Joke hints are now used at most once each when placing hints.

-   Changed: The generator is now more likely to fill the worlds evenly.

-   Fixed: Added proper default nodes for rooms that were missing one, allowing those rooms to be selected as the
    starting room.

-   Fixed: Minimal Checking now correctly handles progressive suit and grapple.

-   Fixed: Config files with invalid JSON are now correctly dealt with.

-   Changed: Improved the performance of the resolver considerably.

-   Added: In the data visualizer, the damage requirements now have more descriptive names.

-   Added: In the data visualizer, requirements are now described with simpler to understand terms.

-   Changed: Windows releases are now created with PyInstaller 3.5.

-   Changed: The generator is now more likely to fill the worlds evenly.

### Logic Database changes

-   Changed: All NTSC-specific tricks are now in logic. These are always in logic, since the fixes from other versions
    are patched out.

-   Changed: Screw Attacking without Space Jump Boots in Hive Temple is no longer required on No Tricks.

-   Changed: In Hive Temple, scan dashing to the door to Temple Security Access is now Hypermode difficulty,
    from Hard and above.

-   Changed: The method to get the Main Research item with only Spider Ball was removed.

-   Fixed: Using charged Light Beam shots to get the item in Hazing Cliff now requires 5 or more Light Ammo.

-   Added: Method to open the gate in Main Reactor with Space Jump Boots and Screw Attack.

-   Changed: Opening the barrier in Crypt with Screw Attack is now always Easy and above.

-   Added: Method to climb to the door to Crypt Tunnel in Crypt via a Bomb Space Jump (Normal and above).

-   Added: Method to open Seeker Launcher blast shields with four missiles, Seeker Launcher, and Screw Attack (Easy
    and above). Underwater, the trick Air Underwater is also required, and the difficulty is Normal and above.

-   Fixed: Dark world damage during the Quadraxis fight is now correctly calculated.

-   Fixed: Requirements for crossing Sacred Path were added.

-   Added: Method to cross gap in the upper level of Command Center using Screw Attack without Space Jump Boots
    (Trivial and above).

-   Added: In Central Mining Station, a method to get to upper door to Command Center Access using a
    Bomb Space Jump (Easy and above) and another using Space Jump Boots and Screw Attack (Easy and above).

-   Added: Methods to climb Mining Plaza using the Morph Ball Bomb (Trivial and above) and using Screw Attack
    without Space Jump Boots (Easy and above).

-   Changed: In Forgotten Bridge, the difficulty of scan dashing to the door to Abandoned Worksite or the portal to
    Dark Forgotten Bridge was lowered to Easy, from Normal.

-   Added: In Forgotten Bridge, a method to get to the door to Grove Access from the portal to Dark Forgotten Bridge
    using only Screw Attack (Easy and above).

-   Added: In Forgotten Bridge, a method to get to the door to Abandoned Worksite via a roll jump (Easy and above).

-   Added: In Forgotten Bridge, a method to get to the bridge center from the door to Grove Access via a scan dash
    (Easy and above).

-   Added: In Hydrodynamo Station, a method to get from the room's top to the door to Save Station B with Screw Attack
    without Space Jump Boots (Trivial and above).

-   Changed: Climbing Hydrodynamo Station with only Gravity Boost and before all three locks are unlocked is now
    Trivial difficulty (from No Tricks).

-   Changed: Getting to the three doors in the middle section of Hydrodynamo Station using Air Underwater is now
    Normal difficulty (from Hard).

-   Fixed: A method to get the item in the Sunburst location by abusing terminal fall now has a damage requirement.

-   Added: A method to get to the turret in Sanctuary Entrance with only Space Jump Boots and Screw Attack, even
    after the bridge is destroyed.

-   Fixed: Lowering the portal barrier in Hive Dynamo Works now requires five missiles.

-   Added: Methods to cross Hive Dynamo Works using a roll jump (Easy and above) and using Space Jump Boots and
    Screw Attack (No Tricks).

-   Added: In Hive Dynamo Works, a method to cross the gap from the door to Hive Dynamo Access by abusing terminal
    fall (Easy and above).

-   Changed: In Hive Dynamo Works, returning from the Flying Ing Cache location using Space Jump Boots and
    Screw Attack is now Trivial difficulty (from Easy).

-   Added: Method to cross Watch Station Access from the door to Main Gyro Chamber using a Bomb Space Jump and
    Screw Attack without Space Jump Boots (Normal and above).

-   Added: In Watch Station Access, method to get from the scan post to the door to Watch Station by bomb jumping
    (Trivial and above) and by using Screw Attack without Space Jump Boots (Easy and above).

-   Fixed: The instant morph into the Morph Ball tunnel in Hall of Honored Dead now lists the Instant Morph trick.

-   Added: Method to get into the Morph Ball tunnel in Hall of Honored Dead using Space Jump Boots and Screw Attack
    (Easy and above).

-   Added: In Phazon Site, methods to get to the door to Bitter Well and to remove the barrier using Screw Attack
    without Space Jump Boots (both Easy difficulty).

-   Changed: The method to go over the Training Chamber statue from the back using Boost Ball and Spider Ball is
    now Normal difficulty (from Hard).

-   Added: In Phazon Site, a method to get to the door to Bitter Well by bomb jumping (Trivial and above).

-   Added: Many connections in Sacrificial Chamber.

-   Added: A method to get to the door to Fortress Transport Access from the top of the statue in Training Chamber
    using only Space Jump Boots (Easy and above). Morph Ball is also required if the statue hasn't been moved.

-   Added: A method to get to the doors to Transit Tunnel West/East in Training Chamber using Air Underwater (Normal
    and above).

-   Fixed: The method to get to the top of the Training Chamber statue using Gravity Boost and Spider Ball now lists
    the Instant Morph trick.

-   Added: In Training Chamber, a method of getting to the top of the statue from the door to Fortress Transport Access
    using just Space Jump Boots (Easy and above).

-   Added: Many connections in Windchamber Gateway.

-   Added: Method to get from the Kinetic Orb Cannon to the door to Transit Tunnel West via Grapple Beam in
    Gathering Hall.

-   Fixed: The slope jump in Abandoned Base now has a damage requirement.

-   Added: Method of getting the Temple Assembly Site item with Screw Attack and without Space Jump Boots.

-   Changed: The slope jump to get to the item in Temple Assembly Site is now Normal difficulty (from Hard).

-   Fixed: Requirements for crossing Dynamo Access were added.

-   Added: In Landing Site, method of reaching the door to Service Access from the Save Station using Space Jump and
    Screw Attack (No Tricks and above).

-   Fixed: The Culling Chamber item now has a damage requirement.

-   Changed: The trick to shoot the Seeker targets in Hive Dynamo Works from the wrong side is now Easy (from Trivial).

-   Fixed: The Watch Station Access roll jump now has a damage requirement.

-   Changed: The Watch Station Access roll jump is now Normal (from Easy).

-   Fixed: Added missing Space Jump Boots requirement for a Bomb Space Jump in Mining Station B.

-   Added: Method to unblock the portal in Mining Station B without Scan Visor (Normal and above).

-   Added: Method to get to the Darkburst location in Mining Station B with just Space Jump Boots and Screw Attack,
    and without using slope jumps or bomb space jumps (Hypermode difficulty).

-   Added: Method to manipulate Power Bomb Guardian into opening the Power Bomb Blast Shield on the door to
    Undertemple Access, using Boost Ball (Normal and above).

-   Fixed: The method to open the Hydrodynamo Station Seeker door using Screw Attack without Seeker Launcher now
    requires Gravity Boost to not have been collected.

-   Added: Method to get to the portal in Mining Station B with Space Jump Boots and Screw Attack (Trivial and above).

-   Fixed: Transport A Access, Collapsed Tunnel, Dynamo Chamber, Trooper Security Station, Mining Station Access, and
    Portal Access A now correctly require Morph Ball.

-   Fixed: Elevator rooms with missing Scan Visor requirements now have them.

-   Fixed: Removed erroneously added method to cross Sanctuary Entrance with Screw Attack without Space Jump Boots.

-   Fixed: Going through Sacred Bridge on No Tricks now requires Scan Visor and Morph Ball when coming from GFMC
    Compound.

-   Added: Method to skip Scan Visor and Morph Ball using Space Jump Boots in Sacred Bridge, when coming from GFMC
    Compound (Easy and above).

-   Fixed: Added Scan Visor requirement in Temple Transport Access (Sanctuary).

-   Changed: Connections in Venomous Pond were redone.

-   Changed: Getting to the door to Dark Transit Station in Trial Grounds with no items is now Hard difficulty, from
    Easy.

-   Added: Methods to get to the door to Dark Transit Station in Trial Grounds with Screw Attack without Space Jump
    Boots (Easy and above) and with a Bomb Space Jump (Normal and above).

-   Fixed: Added missing requirements for the Dark Samus 3 and 4 fight.

-   Changed: Fighting Dark Samus 2 with only Echo Visor is now Trivial difficulty, from Easy.

-   Fixed: Power Bomb doors now require Morph Ball, and Super Missile doors now require Power Beam and Charge Beam.

-   Added: Method to destroy the second web in Hive Tunnel when going through the room backwards using Sonic Boom
    (Easy and above).

## [0.28.1] - 2019-06-14

-   Fixed: Resetting settings would leave the launchers' configuration in an invalid state.

## [0.28.0] - 2019-06-12

-   *Major* - Changed: The resolver now keeps track of current energy during resolution.
    This ensures you'll always have enough Energy Tanks for trips to Dark Aether.

-   *Major* - Added: Scanning a keybearer corpse provides a hint of what is in the matching Flying
    Ing Cache.

-   Added: The tracker now persists the current state.

-   Added: Some generation failures are now automatically retried, using the same permalink.

-   Added: Buttons to see what a difficulty unlocks that doesn't involve tricks at all.

-   Changed: Increased Hint Scan value for logic to the intended value from the previous
    change.

-   Changed: There's no more hints with joke locations.

-   Changed: The lore hint in Mining Station A is now able to be scanned from the room center.

-   Added: A warning is now displayed when trying to disable validation.

-   Fixed: Seeker Missile's included missiles now respect the "needs Missile Launcher"
    option.

-   Changed: Progressive Launcher is now disabled by default.

-   Fixed: Clicking the connection's link in the Data Visualizer should now always work.

-   Changed: Hint Locations page now has a more usable UI.

-   Changed: On No Tricks, the logic will ensure that you can get Missiles, Seeker Launcher, and either
    Grapple Beam or both Space Jump Boots and Screw Attack before fighting Chykka.

-   Added: Methods to cross Workers Path with Screw Attack.

## [0.27.1] - 2019-05-30

-   Fixed: Specific trick levels are now persisted correctly across multiple sessions.

## [0.27.0] - 2019-05-28

-   *Major* - Changed: Optimized the seed generation step. It should now take roughly
    half as long or even faster.

-   *Major* - Added: It's now possible to configure the difficulty on a per-trick basis.

-   *Major* - Added: It's now possible to check where a certain trick is used on each
    difficulty.

-   Added: Hint Scans are valued more by the logic, making Translators more likely.

-   Changed: Joke item and locations now have a `(?)` added to make then slightly more
    obvious they're not serious.

-   Changed: Average ammo provided per expansion is now shown with more precision.

-   Added: `randovania echoes database list-dangerous-usage` command to list all
    paths that require a resource to not be collected.

-   Added: Methods to get to Sunburst location by reaching the platform with the cannon
    with a scan dash (Normal and above) or with just Space Jump Boots (Easy and above).

-   Added: Method to leave and enter the arena in Agon Temple with only Space Jump Boots
    (Trivial and above to enter; Easy and above to leave).

-   Added: Method to get to Darkburst location in Mining Station B via a Bomb Space Jump
    and without Screw Attack (Easy and above).

-   Fixed: In Hydrodynamo Station, going from the door to Hydrodynamo Shaft to the door to
    Save Station B now always requires all three locks in Hydrodynamo Station to be unlocked.

-   Added: Method to cross Phazon Pit using a Bomb Space Jump (Easy and above).

-   Added: Method to open the Seeker door in Hydrodynamo Station without the Seeker Launcher,
    using Screw Attack and one missile (Hard and Above).

-   Changed: The Ing Windchamber puzzle now only requires four missiles instead of five.

-   Changed: The cannon in Sanctuary Temple Access now only requires four missiles to
    activate instead of five.

-   Changed: Sanctuary Temple Access now requires a way to defeat the Quad to get through.

-   Added: Support for damage requirements without exactly one damage reduction item.

-   Changed: Seed validation should run faster and with fewer errors now.

-   Added: Another joke hint.

-   Changed: Updated credits.

-   Fixed: Crossing Sanctuary Entrance via the Spider Ball Track now requires Boost Ball.

-   Added: Method to cross Sanctuary Entrance with Screw Attack and without Space Jump Boots
    (Trivial and above).

-   Added: Method to cross Sanctuary Entrance, from the door to Power Junction to the door to
    Temple Transport Access, with Spider Ball and Power Bombs (Easy and above).

-   Fixed: The method to get the Sanctuary Entrance item without Spider Ball now requires
    Spider Guardian to not have been defeated.

-   Added: Method to get to and use the Vigilance Class Turret in Sanctuary Entrance using
    Space Jump Boots, Screw Attack, and Spider Ball. Spider Ball isn't required if Spider
    Guardian hasn't been defeated.

-   Fixed: In Sanctuary Entrance, going up the Spider Ball Track near the lore scan via the
    intended method now requires Boost Ball and the Morph Ball Bomb.

-   Added: Methods to go up the Spider Ball Track near the lore scan in Sanctuary Entrance
    with Spider Ball and only one of the following items:
    - Morph Ball Bomb (Trivial and above);
    - Boost Ball (Trivial and above);
    - Space Jump Boots (Easy and above).

-   Changed: In Sanctuary Temple, getting to the door to Controller Access via scan dashing
    is now Hard and above, from Normal and above.

-   Added: A tab with all change logs.

## [0.26.3] - 2019-05-10

-   Changed: Tracker now raises an error if the current configuration is unsupported.

-   Fixed: Tracker no longer shows an error when opening.

## [0.26.2] - 2019-05-07

-   Fixed: An empty box no longer shows up when starting a game with no
    extra starting items.

-   Fixed: A potential crash involving HUD Memos when a game is randomized
    multiple times.


## [0.26.1] - 2019-05-05

-   Fixed: The in-app changelog and new version checker now works again.

-   Fixed: Patching with HUD text on and using expansions locked by major item now works.

-   Changed: Missile target default is now 175, since Seeker Launcher now defaults to
    giving 5 missiles.


## [0.26.0] - 2019-05-05

-   **MAJOR** - Added: Option to require Missile Launcher and main Power Bombs for the
    respective expansions to work.

-   **MAJOR** - Added: Option to change which translator each translator gate in the
    game needs, including choosing a random one.

-   **MAJOR** - Added: Luminoth Lore scans now includes hints for where major items
    are located, as well as what the Temple Guardians bosses drop and vanilla Light Suit.

-   Added: Welcome tab, with instructions on how to use Randovania.

-   Added: Option to specify how many items Randovania will randomly place on your
    starting inventory.

-   Added: Option to change how much damage you take from Dark Aether when using
    Varia Suit and Dark Suit.

-   Added: Progressive Launcher: a progression between Missile Launcher and Seeker Launcher.

-   Changed: Logic considers the Translator Gates in GFMC Compound and Torvus Temple
    to be up from the start, preventing potential softlocks.

-   Changed: Escaping Main Hydrochamber after the Alpha Blogg with a Roll Jump is
    now Hard and above, from Easy and above.

-   Changed: The no-Boost return method in Dark Arena Tunnel is now Normal and above only.

-   Changed: The Slope Jump method in Great Bridge for Abandoned Worksite is now Hard
    and above, from Normal.

-   Changed: Crossing the statue in Training Chamber before it's moved with Boost and
    Spider is now Hard and above, from Hypermode.

-   Added: Option to disable the Sky Temple Key hints or to hide the Area name.

-   Changed: The location in the Sky Temple Key hint is now colored.

-   Changed: There can now be a total of 99 of any single Major Item, up from 9.

-   Changed: Improved elevator room names. There's now a short and clear name for all
    elevators.

-   Changed: The changed room names now apply for when elevators are vanilla as well.

-   Fixed: Going from randomized elevators to vanilla elevators no longer requires a
    clean unpack.

-   Added: `randovania echoes database list-resource-usage` now supports all types of
    resources.

-   Added: `list-resource-usage` and `list-difficulty-usage` now has the `--print-only-area`
    argument.

-   Changed: Areas with names starting with !! are now hidden in the Data Visualizer.

-   Added: Docks and Elevators now have usable links in the Data Visualizer. These links
    brings you to the matching node.

-   Added: The message when collecting the item in Mining Station B now displays when in
    the wrong layer.

-   Added: A warning now shows when going on top of the ship in GFMC Compound before
    beating Jump Guardian.

## [0.25.0] - 2019-03-24

-   Changed: Reworked requirements for getting the Missile in Crossroads from the doors. You can:
    - On Normal and above, with Boost, Bombs, Space Jump and Screw Attack
    - On Hard and above, with Bombs, Space Jump and Screw Attack
    - On Hypermode, with Bombs and Space Jump

-   Changed: Logic requirements for Dark Samus 2 fight are now the following:
    - On all trick levels, Dark Visor
    - On Easy and above, Echo Visor
    - On Normal and above, no items

-   Changed: The Slope Jump in Temple Assembly Site is now Hard and above, from Normal and above.

-   Changed: All occurrences of Wall Boost are now locked behind Hard or above.

-   Added: Added method to get the Power Bomb in Sanctuary Entrance with just Space Jump
    and Screw Attack. (See [#29](https://github.com/randovania/randovania/issues/29))

-   Added: Added method to cross Dark Arena Tunnel in the other direction without Boost.
    (See [#47](https://github.com/randovania/randovania/issues/47))

-   Added: Basic support for running Randovania on non-Windows platforms.

-   Added: You can now create Generic Nodes in the Data Editor.

-   Changed: Drop down selection of resources are now sorted in the Data Editor.

-   Changed: Shareable hash is now based only on the game modifications part of the seed log.

-   Fixed: Python wheel wasn't including required files due to mising \_\_init__.py

-   Fixed: error when shuffling more than 2 copies of any Major Item

-   Fixed: permalinks were using the the ammo id instead of the configured

## [0.24.1] - 2019-03-22

-    **MAJOR**: New configuration GUI for Major Items:
     - For each item, you can now choose between:
        - You start with it
        - It's in the vanilla location
        - It's shuffled and how many copies there are
        - It's missing
     - Configure how much beam ammo Light Beam, Dark Beam and Annihilator Beam gives when picked.
        - The same for Seeker Launcher and missiles.

-    **MAJOR**: New configuration GUI for Ammo:
     - For each ammo type, you choose a target total count and how many pickups there will be.

        Randovania will ensure if you collect every single pickup and every major item that gives
        that ammo, you'll have the target total count.

-    **MAJOR**: Added progressive items. These items gives different items when you collect then,
        based on how many you've already collected. There are two:
     - Progressive Suit: Gives Dark Suit and then Light Suit.
     - Progressive Grapple: Gives Grapple Beam and then Screw Attack.

-    **MAJOR**: Add option to split the Beam Ammo Expansion into a Dark Ammo Expansion and
        Light Ammo Expansion.

        By default there's 10 of each, with less missiles instead.


-    **MAJOR**: Improvements for accessibility:
     - All translator gates are now colored with the correct translator gate color they need.
     - Translators you have now show up under "Visors" in the inventory menu.
     - An option to start the game with all maps open, as if you used all map stations.
     - An option to add pickup markers on the map, that identifies where items are and if
        you've collected them already.
     - When elevators are randomized, the room name in the map now says where that elevator goes.
     - Changed the model for the Translator pickups: now the translator color is very prominent and easy to identify.

-    Added: Option to choose where you start the game

-    Added: Option to hide what items are, going from just changing the model, to including the
    scan and even the pickup text.

     You can choose to replace the model with ETM or with a random other item, for even more troll.

-    Added: Configure how many count of how many Sky Temple Keys you need to finish the game

-    Changed: Choosing "All Guardians" only 3 keys now

-    Changed: Timeout for generating a seed is now 5 minutes, up from 2.

0.24.0 was a beta only version.

## [0.23.0] - 2019-02-10

-   Added: New option to enable the "Warp to Start" feature.
-   Added: A "What's new" popup is displayed when launching a new version for the first time.
-   Fixed: changed text in Logic Settings to mention there _are_ hints for Sky Temple Keys.
-   Changed: Updated Claris' Randomizer, for the following fixes:
    -   Added the ability to warp to the starting room from save stations (-t).
    -   Major bug fix: The game will no longer immediately crash when not playing with Menu Mod.

## [0.22.0] - 2019-02-06

-   Changed: "Faster credits" and "Skip item acquisitions popups" are no longer included in permalinks.
-   Changed: Updated Claris' Randomizer, for the following fixes:
    -   Fixed an issue with two of the Sky Temple Key hints being accidentally switched.
    -   FrontEnd editing now works properly for PAL and Japanese versions.
    -   Attract video removal is now integrated directly into the Randomizer.
    -   Getting the Torvus Energy Controller item will no longer block you from getting the Torvus Temple item.

## [0.21.0] - 2019-01-31

-   **Major**: now using Claris' Randomizer version 4.0. See [Changelog](https://pastebin.com/HdK9jdps).

-   Added: Randovania now changes the game id to G2ME0R, ensuring it has different saves.
-   Added: Game name is now changed to 'Metroid Prime 2: Randomizer - SEEDHASH'. Seed hash is a 8 letter/number
      combination that identifies the seed being played.
-   Changed: the ISO name now uses the seed hash instead of the permalink. This avoids issues with the permalink containing /
-   Changed: Removed Agon Temple door lock after fighting Bomb Guardian, since this has been fixed in the Randomizer.
-   Fixed: Selecting an non-existent directory for Output Directory had inconsistent results

## [0.20.2] - 2019-01-26

-   Fixed: changed release zip to not use BZIP2. This fixes the native windows zip client being unable to extract.

0.20.1 was skipped due to technical issues.

## [0.20.0] - 2019-01-13

-   Added: an icon! Thanks to Dyceron for the icon.
-   Added: a simple Tracker to allow knowing where you can go with a given item state
-   Changed: Don't consider that Seeker Launcher give missiles for logic, so it's never
      considered a missile source.

## [0.19.1] - 2019-01-06

-   Fixed: Hydrodynamo Station's Door to Training Access now correctly needs Seekers
-   Added: New alternatives with tricks to get the pickup in Mining Plaza A.
-   Added: Trick to cross the Mining Plaza A backwards while it's closed.
-   Changed: Added a chance for Temple Keys not being always placed last.
-   Changed: Light Suit now has a decreased chance of being placed early.

0.19.0 was skipped due to technical issues.

## [0.18.0] - 2019-01-02

-   Added: Editor for Randovania's database. This allows for modifications and contributions to be made easily.
      There's currently no way to use the modified database directly.
-   Added: Options to place the Sky Temple Keys on Guardians + Sub-Guardians or just on Guardians.
-   Changed: Removed Space Jump method from Training Chamber.
-   Changed: Added Power Bomb as option for pickup in Hive Chamber B.
-   Changed: Shortened Permalinks when pickup quantities aren't customized.
-   Added: Permalinks now include the database version they were created for.
-   Fixed: Logic mistake in item distribution that made some impossible seeds.
-   Changed: For now, don't consider Chykka a "can only do once" event, since Floaty is not used.
-   Fixed: Permalinks now properly ignore the Energy Transfer Module.

## [0.17.2] - 2018-12-27

-   Fixed: 'Clear loaded game' now properly does it's job.
-   Changed: Add an error message to capture potential Randomizer failures.
-   Changed: Improved README.

## [0.17.1] - 2018-12-24

-   Fixed: stray tooltips in GUI elements were removed.
-   Fixed: multiple typos in GUI elements.

## [0.17.0] - 2018-12-23

-   New: Reorganized GUI!
    -   Seed Details and Data Visualizer are now different windows opened via the menu bar.
    -   There are now three tabs: ROM Settings, Logic Settings and Item Quantities.
-   New: Option to disable generating an spoiler.
-   New: All options can now be exported and imported via a permalink.
-   Changed: Renamed "Logic" to "Trick Level" and "No Glitches" to "No Tricks". Appropriate labels in the GUI and files
    changed to match.
-   Internal: no longer using the py.path and dataset libraries

## [0.16.2] - 2018-12-01

-   Fixed: adding multiples of an item now works properly.

## [0.16.1] - 2018-11-25

-   Fixed: pressing the Reset button in the Item Quantity works properly.
-   Fixed: hiding help in Layout Generation will no longer hide the item names in Item Quantity.

## [0.16.0] - 2018-11-20

-   Updated item distribution: seeds are now less likely to have all items in the beginning, and some items less likely to appear in vanilla locations.
-   Item Mode (Standard/Major Items) removed for now.

## [0.15.0] - 2018-10-27

-   Added a timeout of 2 minutes to seed generation.
-   Added two new difficulties:
    -   Trivial: An expansion of No Glitches, where no tricks are used but some clever abuse of room layouts are used.
    -   Hypermode: The highest difficulty tricks, mostly including ways to skip Space Jump, are now exclusive to this difficulty.
-   Removed Controller Reset tricks. This trick doesn't work with Nintendont. This will return later as an additional configuration.

## [0.14.0] - 2018-10-07

-   **Major**: Added support for randomizing elevators.
-   Fixed spin boxes for item quantities changing while user scrolled the window.
    It is now needed to click on them before using the mouse wheel to change their values.
-   Fixed some texts being truncated in the Layout Generation window.
-   Fixed generation failing when adding multiple of some items.
-   Added links to where to find the Menu Mod.
-   Changed the order of some fields in the Seed Log.

## [0.13.2] - 2018-06-28

-   Fixed logic missing Amber Translator being required to pass by Path of Eyes.

## [0.13.1] - 2018-06-27

-   Fixed logic errors due to inability to reload Main Reactor after defeating Dark Samus 1.
-   Added prefix when loading resources based on type, improving logs and Data Visualizer.

## [0.13.0] - 2018-06-26

-   Added new logic: "Minimal Validation". This logic only checks if Dark Visor, Light Suit and Screw Attack won't lock each other.
-   Added option to include the Claris' Menu Mod to the ISO.
-   Added option to control how many of each item is added to the game.

## [0.12.0] - 2018-09-23

-   Improved GUI usability
-   Fixed Workers Path not requiring Cobalt Translator to enter

## [0.11.0] - 2018-07-30

-   Randovania should no longe create invalid ISOs when the game files are bigger than the maximum ISO size: an error is properly reported in that case.
-   When exporting a Metroid Prime 2: Echoes ISO if the maximum size is reached there's is now an automatic attempt to fix the issue by running Claris' "Disable Echoes Attract Videos" tool from the Menu Mod.
-   The layout log is automatically added to the game's files when randomizing.
-   Simplified ISO patching: by default, Randovania now asks for an input ISO and an output path and does everything else automatically.

## [0.10.0] - 2018-07-15

-   This release includes the capability to generate layouts from scratch and these to the game, skipping the entire searching step!

## [0.9.2] - 2018-07-10

-   Added: After killing Bomb Guardian, collecting the pickup from Agon Energy Controller is necessary to unlock the Agon Temple door to Temple Access.
-   Added a version check. Once a day, the application will check GitHub if there's a new version.
-   Preview feature: option to create item layouts, instead of searching for seeds. This is much more CPU friendly and faster than searching for seeds, but is currently experimental: generation is prone to errors and items concentrated in early locations. To use, open with randovania.exe gui --preview from a terminal. Even though there are many configuration options, only the Item Loss makes any difference.

## [0.9.1] - 2018-07-21

-   Fixed the Ing Cache in Accursed Lake didn't need Dark Visor.

## [0.9.0] - 2018-05-31

-   Added a fully featured GUI.

## [0.8.2] - 2017-10-19

-   Stupid mistake.

## [0.8.1] - 2017-10-19

-   Fix previous release.

## [0.8.0] - 2017-10-19

-   Save preferences.
-   Added Claris Randomizer to the binary release.

## [0.7.1] - 2017-10-17

-   Fixed the interactive .bat

## [0.7.0] - 2017-10-14

-   Added an interactive shell.
-   Releases now include the README.

## [0.5.0] - 2017-10-10

-   Releases now include standalone windows binaries
