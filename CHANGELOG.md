# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [Unreleased]

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
    KNOW ISSUE: While scanning something, the categories that show up are incorrect.

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

-   Added: In Main Gyro Chamber, a method of reaching the bottom of the gyro area from the middle of the room with Screw Attack (Easy and aboive).

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
