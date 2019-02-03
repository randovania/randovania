Pickup Randomizer for Metroid Prime and Metroid Prime 2: Echoes, created by Claris.

1. ABOUT
2. PREREQUISITES
3. PROGRAM USAGE
4. VERSION HISTORY
5. PICKUP LISTS



1. ABOUT

The Randomizer switches around the locations of all pickups/expansions. This includes:
- Each pickup's properties, model, dialog box, jingle, etc. are all changed to the new pickup's.
- The pickup's position is adjusted, as otherwise some pickups are naturally higher/lower than others.
- The cutscene when collecting a previously major pickup is removed; it would still play the cutscene for the original pickup, which would make no sense with the new pickup.
- Adds/removes layer switches for Artifacts/Old-Artifacts, so that Artifacts properly activate Artifact Temple (and their replacements do not). Also adds/removes the automatic pause after collecting an Artifact.
- The Phazon Suit and Translator pickups are given custom models, as they do not have unique models in the original games.

Known issues:
- Echoes may be too large after running the Randomizer to properly rebuild/run on console. You can try using the included "Disable Echoes Attract Videos" program, which removes the title screen attract videos. Another solution is to remove the Multiplayer music (files multi-defbgm32.dsp and/or multiplay9-32-3.dsp in the Audio folder; either delete them outright, or replace them with a blank file if required by your rebuilding method).
- The Randomizer is not guaranteed to be completable; there are currently no checks to ensure items are not placed in impossible-to-obtain locations (for example, Supers/Charge behind Cordite, or Dark Visor in an Ing Cache).
- The Translator pickups in Echoes do not have their scans added to a SAVW, as the game would think existing saves are corrupt; because of this, scanning Translators may sometimes have issues.

Thanks to:
- Aruki, who has been a major help in learning how to modify the game/understanding the file formats/etc.
- xinoea for creating the texture for the custom Phazon Suit model.
- Jordan Rinehart (French/Japanese), HatWolf (German), Dario FF (Spanish), and LetsPlayNintendoITA (Italian) for translating the Temple Key strings.

NOTE: You should not use an already created save with the Randomizer (i.e. a [Starting World] 00% 00:00 save). Due to changes to room layers, you should always use a new save, even between different randomizations.



2. PREREQUISITES

The Randomizer does not edit an ISO directly; you need to extract the files from the Prime or Echoes ISO. This can be done with Dolphin (right-click the game > Filesystem > right-click Disc > Extract All Files...), or using a program such as GC Rebuilder.



3. PROGRAM USAGE

Randomizer [Folder] -g [MP1/MP2] -s [Seed] -e [Excluded Pickups] [Options]

[Folder]: The folder containing the game's files to randomize.

-g [MP1/MP2]: The game you wish to randomize. If not provided, the Randomizer will attempt to open Metroid2.pak and check the version of the game there.

-s [Seed]: The random seed, if you wish to reuse a previous randomization. The seed must be between 0 and 2147483647. Note that using a different excluded pickup list, or a different version of the Randomizer, will likely give a different result.

-e [Excluded Pickups]: Pickups that should not be randomized. Use the pickup numbers listed at the bottom of the readme, separated by commas with no spaces; for example, "-e 5,19,28" would exclude the Morph Ball, Missile Launcher, and Bombs in Prime. If not given, then by default Prime excludes Morph Ball, Missile Launcher, and Bombs; Echoes excludes the Violet Translator. If you wish to randomize every pickup, enter "-e none" instead.

Options: -hivw

-h: HUD Memo Popup Removal. Changes the type of HUD Memo used for pickups, to remove the popup. Also removes Artifact pauses in Prime. Note that certain pickups that immediately play a cutscene will not have their popup removed.

-i: Item Loss Removal. In Prime, this gives you the same items you start with on the Frigate when you land on Tallon. In Echoes, this switches the layers in Hive Chamber B, so the room is in its post-Item Loss state.

-v: Elevator Randomization Mode: Randomizes how elevators are connected to each other. Cannot connect an elevator to a different elevator in the same world. In Prime, if Morph Ball or Bombs are excluded, the first elevator connecting Tallon Overworld and Chozo Ruins will not be changed.

-w: Random Warp Mode. The game will warp you to a random room every time you collect an unexcluded pickup. Prime cannot warp you to the Frigate or Impact Crater; Echoes cannot warp you to the Sky Temple or rooms used solely for cutscenes.



4. VERSION HISTORY

v4.0
- Fixed various issues with multiple copies of the same pickup.
- Starting the Dark Samus 1 fight disables adjacent rooms from loading automatically (fixes a potential crash).
- Beating Dark Samus 1 will now turn off the first pass pirates layer in Biostorage Station (fixes a potential crash).
- Agon Temple's first door no longer stays locked after Bomb Guardian until you get the Agon Energy Controller item.
- Leaving during the Grapple Guardian fight no longer causes Grapple Guardian to not drop an item if you come back and fight it again.
- Undertemple Access's default spawn point has been moved in-bounds.
- The Luminoth barriers that appear on certain doors after collecting or returning a world's energy have been removed.
- Cutscenes are now always skippable, even on a brand new save file.
- Translator pickup scans are added to the save, fixing potential issues with scanning them.
- Percent is calculated by how many items there are that count for percent, so 100% will be "all percent increasing items" no matter the quantity of them.
- Credits are now optionally sped up to be 60 seconds long (over 4x faster).
- Removed some instances in Main Research, to decrease the chance of a crash coming from Central Area Transport West. Also fixed leaving the room midway through destroying the echo locks making it impossible to complete.
- The scans in Sky Temple Gateway now tell you the location of each Sky Temple Key.
- Power Bombs no longer instantly kill either Alpha Splinter's first phase or Spider Guardian (doing so would not actually end the fight, leaving you stuck).
- Hard Mode is now immediately unlocked on a new save file.


V3.2 - May 15th, 2016
General:
- Elevator Randomization Mode option added. (-v)
- Pickups now retain the original pickup's collision.

Prime-specific:
- The Phazon Suit pickup's scale is reduced, to match the Varia and Gravity pickups.
- The Thermal Visor plays a sound effect when collected.

Echoes-specific:
- Pickups replacing Translators are no longer potentially duplicated.


V3.1 - January 26th, 2016
Random Warp Mode actually runs now.


V3.0 - December 14th, 2015
General:
- The Prime and Echoes Randomizers have been combined into a single program, and rewritten almost entirely from scratch.
- Additional instances and pickup assets are now put on their own newly-created layer instead of an existing layer (mostly; the Energy Transfer Module requires instances added on the same layer as the pickup to work properly).
- HUD Memo Popup Removal option added. (-h)
- The Mission Final screen displays the Randomizer version and Seed.
- Pickup positions are now adjusted horizontally in addition to vertically. Only really matters for Keys in Echoes.
- Various other minor unimportant changes.

Prime-specific:
- Item Loss Removal option added, to match with Echoes. (-i)
- If an Artifact replaces Main Power Bombs or the Phazon Suit, the game now pauses at the correct time.

Echoes-specific:
- Translators are now randomized. Their model is the Scan Visor used in the logbook, with the inner section colored the Translator's color. A pickup has been added in each Energy Controller instead of scanning the hologram.
- Violet Translator is excluded by default, to make navigating Temple Grounds at the start of the game a lot easier.
- The Energy Transfer Module is now moved correctly (was previously invisible and potentially game-crashing), and is no longer excluded by default.
- Random Warp option added, to match with Prime. (-w)
- Fixed a crash when obtaining Grapple outside of Torvus on PAL.
- The Light Suit and Translators will reset any ConditionalRelays used in the room or adjacent rooms, so you can't get stuck under Dark Water or behind a Translator Gate after obtaining them.
- The cutscenes before the pickups in Dark Torvus Temple and Main Gyro Chamber now show the correct randomized pickup.
- Removed "Randomize Music" and "Enable Pickup Cutscenes" options as they were pretty useless.


Prime V2.0 - August 23rd, 2014
Randomizer additions:
- .pak files are now edited directly; unpacking/repacking them is no longer necessary.
- Versions other than NTSC 0-00 are now supported. However, they have not been thoroughly tested, so use at your own risk; NTSC 0-00 is the recommended version to use.
- Random Warp option added, making the game warp you to a random room in the 5 main areas after collecting unexcluded pickups.
- Log file format updated, aligning each column and removing the original pickup.
- Creates a folder for log files inside the Randomizer's folder if it does not already exist.

In-Game fixes:
- Artifact of Truth is now required to beat the game, and is no longer excluded by default.
- Cutscene skips updated, getting rid of the .6 second loss of control after getting a major pickup among other things.
- If Artifact Temple has an artifact, its layer is turned on by default, so the room doesn't have to be reloaded to trigger Ridley if collected last.
- Artifacts now pause the game, while pickups replacing Artifacts do not.
- Fixed the cutscene skip for pickups replacing Wave and X-Ray, so they now have the HUD Memo popup.
- Pickups replacing Varia and Gravity now play the correct jingle.
- Pickups retain the original pickup's fade-in (used for pickups replacing Wild, Warrior, and Spider).
- Pickup positions slightly adjusted; positions were previously based on their bottom, while now they're based on their center.


Echoes V1.0 - August 8th, 2014
Initial Public Release


Prime V1.0 - June 21st, 2014
Initial Public Release



5. PICKUP LISTS

Prime
 0: Chozo - - - Main Plaza (Half-Pipe) - - - - - - - - Missile Expansion 1
 1: Chozo - - - Main Plaza (Grapple Ledge) - - - - - - Missile Expansion 2
 2: Chozo - - - Main Plaza (Tree)  - - - - - - - - - - Missile Expansion 3
 3: Chozo - - - Main Plaza (Locked Door) - - - - - - - Energy Tank 1
 4: Chozo - - - Ruined Fountain  - - - - - - - - - - - Missile Expansion 4
 5: Chozo - - - Ruined Shrine ("Beetle Battle")  - - - Morph Ball
 6: Chozo - - - Ruined Shrine (Half-Pipe)  - - - - - - Missile Expansion 5
 7: Chozo - - - Ruined Shrine (Lower Tunnel) - - - - - Missile Expansion 6
 8: Chozo - - - Vault  - - - - - - - - - - - - - - - - Missile Expansion 7
 9: Chozo - - - Training Chamber - - - - - - - - - - - Energy Tank 2
10: Chozo - - - Ruined Nursery - - - - - - - - - - - - Missile Expansion 8
11: Chozo - - - Training Chamber Access  - - - - - - - Missile Expansion 9
12: Chozo - - - Magma Pool - - - - - - - - - - - - - - Power Bomb Expansion 1
13: Chozo - - - Tower of Light - - - - - - - - - - - - Wavebuster
14: Chozo - - - Tower Chamber  - - - - - - - - - - - - Artifact of Lifegiver
15: Chozo - - - Ruined Gallery (Missile Wall)  - - - - Missile Expansion 10
16: Chozo - - - Ruined Gallery (Tunnel)  - - - - - - - Missile Expansion 11
17: Chozo - - - Transport Access North - - - - - - - - Energy Tank 3
18: Chozo - - - Gathering Hall - - - - - - - - - - - - Missile Expansion 12
19: Chozo - - - Hive Totem - - - - - - - - - - - - - - Missile Launcher
20: Chozo - - - Sunchamber (Flaahgra)  - - - - - - - - Varia Suit
21: Chozo - - - Sunchamber (Ghosts)  - - - - - - - - - Artifact of Wild
22: Chozo - - - Watery Hall Access - - - - - - - - - - Missile Expansion 13
23: Chozo - - - Watery Hall (Scan Puzzle)  - - - - - - Charge Beam
24: Chozo - - - Watery Hall (Underwater) - - - - - - - Missile Expansion 14
25: Chozo - - - Dynamo (Lower) - - - - - - - - - - - - Missile Expansion 15
26: Chozo - - - Dynamo (Spider Track)  - - - - - - - - Missile Expansion 16
27: Chozo - - - Burn Dome (Missile)  - - - - - - - - - Missile Expansion 17
28: Chozo - - - Burn Dome (I. Drone) - - - - - - - - - Morph Ball Bomb
29: Chozo - - - Furnace (Spider Tracks)  - - - - - - - Missile Expansion 18
30: Chozo - - - Furnace (Inside Furnace) - - - - - - - Energy Tank 4
31: Chozo - - - Hall of the Elders - - - - - - - - - - Energy Tank 5
32: Chozo - - - Crossway - - - - - - - - - - - - - - - Missile Expansion 19
33: Chozo - - - Elder Chamber  - - - - - - - - - - - - Artifact of World
34: Chozo - - - Antechamber  - - - - - - - - - - - - - Ice Beam
35: Phendrana - Phendrana Shorelines (Behind Ice)  - - Missile Expansion 20
36: Phendrana - Phendrana Shorelines (Spider Track)  - Missile Expansion 21
37: Phendrana - Chozo Ice Temple - - - - - - - - - - - Artifact of Sun
38: Phendrana - Ice Ruins West - - - - - - - - - - - - Power Bomb Expansion 2
39: Phendrana - Ice Ruins East (Behind Ice)  - - - - - Missile Expansion 22
40: Phendrana - Ice Ruins East (Spider Track)  - - - - Missile Expansion 23
41: Phendrana - Chapel of the Elders - - - - - - - - - Wave Beam
42: Phendrana - Ruined Courtyard - - - - - - - - - - - Energy Tank 6
43: Phendrana - Phendrana Canyon - - - - - - - - - - - Boost Ball
44: Phendrana - Quarantine Cave  - - - - - - - - - - - Spider Ball
45: Phendrana - Research Lab Hydra - - - - - - - - - - Missile Expansion 24
46: Phendrana - Quarantine Monitor - - - - - - - - - - Missile Expansion 25
47: Phendrana - Observatory  - - - - - - - - - - - - - Super Missile
48: Phendrana - Transport Access - - - - - - - - - - - Energy Tank 7
49: Phendrana - Control Tower  - - - - - - - - - - - - Artifact of Elder
50: Phendrana - Research Core  - - - - - - - - - - - - Thermal Visor
51: Phendrana - Frost Cave - - - - - - - - - - - - - - Missile Expansion 26
52: Phendrana - Research Lab Aether (Tank) - - - - - - Energy Tank 8
53: Phendrana - Research Lab Aether (Morph Track)  - - Missile Expansion 27
54: Phendrana - Gravity Chamber (Underwater) - - - - - Gravity Suit
55: Phendrana - Gravity Chamber (Grapple Ledge)  - - - Missile Expansion 28
56: Phendrana - Storage Cave - - - - - - - - - - - - - Artifact of Spirit
57: Phendrana - Security Cave  - - - - - - - - - - - - Power Bomb Expansion 3
58: Tallon  - - Landing Site - - - - - - - - - - - - - Missile Expansion 29
59: Tallon  - - Alcove - - - - - - - - - - - - - - - - Space Jump Boots
60: Tallon  - - Frigate Crash Site - - - - - - - - - - Missile Expansion 30
61: Tallon  - - Overgrown Cavern - - - - - - - - - - - Missile Expansion 31
62: Tallon  - - Root Cave  - - - - - - - - - - - - - - Missile Expansion 32
63: Tallon  - - Artifact Temple  - - - - - - - - - - - Artifact of Truth
64: Tallon  - - Transport Tunnel B - - - - - - - - - - Missile Expansion 33
65: Tallon  - - Arbor Chamber  - - - - - - - - - - - - Missile Expansion 34
66: Tallon  - - Cargo Freight Lift to Deck Gamma - - - Energy Tank 9
67: Tallon  - - Biohazard Containment  - - - - - - - - Missile Expansion 35
68: Tallon  - - Hydro Access Tunnel  - - - - - - - - - Energy Tank 10
69: Tallon  - - Great Tree Chamber - - - - - - - - - - Missile Expansion 36
70: Tallon  - - Life Grove Tunnel  - - - - - - - - - - Missile Expansion 37
71: Tallon  - - Life Grove (Start) - - - - - - - - - - X-Ray Visor
72: Tallon  - - Life Grove (Underwater Spinner)  - - - Artifact of Chozo
73: Mines - - - Main Quarry  - - - - - - - - - - - - - Missile Expansion 38
74: Mines - - - Security Access A  - - - - - - - - - - Missile Expansion 39
75: Mines - - - Storage Depot B  - - - - - - - - - - - Grapple Beam
76: Mines - - - Storage Depot A  - - - - - - - - - - - Flamethrower
77: Mines - - - Elite Research (Phazon Elite)  - - - - Artifact of Warrior
78: Mines - - - Elite Research (Laser) - - - - - - - - Missile Expansion 40
79: Mines - - - Elite Control Access - - - - - - - - - Missile Expansion 41
80: Mines - - - Ventilation Shaft  - - - - - - - - - - Energy Tank 11
81: Mines - - - Phazon Processing Center - - - - - - - Missile Expansion 42
82: Mines - - - Processing Center Access - - - - - - - Energy Tank 12
83: Mines - - - Elite Quarters - - - - - - - - - - - - Phazon Suit
84: Mines - - - Central Dynamo - - - - - - - - - - - - Power Bomb
85: Mines - - - Metroid Quarantine B - - - - - - - - - Missile Expansion 43
86: Mines - - - Metroid Quarantine A - - - - - - - - - Missile Expansion 44
87: Mines - - - Fungal Hall B  - - - - - - - - - - - - Missile Expansion 45
88: Mines - - - Phazon Mining Tunnel - - - - - - - - - Artifact of Newborn
89: Mines - - - Fungal Hall Access - - - - - - - - - - Missile Expansion 46
90: Magmoor - - Lava Lake  - - - - - - - - - - - - - - Artifact of Nature
91: Magmoor - - Triclops Pit - - - - - - - - - - - - - Missile Expansion 47
92: Magmoor - - Storage Cavern - - - - - - - - - - - - Missile Expansion 48
93: Magmoor - - Transport Tunnel A - - - - - - - - - - Energy Tank 13
94: Magmoor - - Warrior Shrine - - - - - - - - - - - - Artifact of Strength
95: Magmoor - - Shore Tunnel - - - - - - - - - - - - - Ice Spreader
96: Magmoor - - Fiery Shores (Morph Track) - - - - - - Missile Expansion 49
97: Magmoor - - Fiery Shores (Warrior Shrine Tunnel) - Power Bomb Expansion 4
98: Magmoor - - Plasma Processing  - - - - - - - - - - Plasma Beam
99: Magmoor - - Magmoor Workstation  - - - - - - - - - Energy Tank 14

Echoes
  0: Temple Grounds - - - Hive Chamber A  - - - - - - - Missile Expansion 1
  1: Temple Grounds - - - Hall of Honored Dead  - - - - Seeker Launcher
  2: Temple Grounds - - - Hive Chamber B  - - - - - - - Missile Expansion 2
  3: Temple Grounds - - - War Ritual Grounds  - - - - - Missile Expansion 3
  4: Temple Grounds - - - Windchamber Gateway - - - - - Energy Tank 1
  5: Temple Grounds - - - Transport to Agon Wastes  - - Missile Expansion 4
  6: Temple Grounds - - - Temple Assembly Site  - - - - Missile Expansion 5
  7: Temple Grounds - - - Grand Windchamber - - - - - - Sunburst
  8: Temple Grounds - - - Dynamo Chamber  - - - - - - - Power Bomb Expansion 1
  9: Temple Grounds - - - Storage Cavern B  - - - - - - Energy Tank 2
 10: Temple Grounds - - - Plain of Dark Worship - - - - Missile Expansion 6
 11: Temple Grounds - - - Defiled Shrine  - - - - - - - Sky Temple Key 8
 12: Temple Grounds - - - Communication Area  - - - - - Missile Expansion 7
 13: Temple Grounds - - - GFMC Compound - - - - - - - - Missile Launcher
 14: Temple Grounds - - - GFMC Compound - - - - - - - - Missile Expansion 8
 15: Temple Grounds - - - Accursed Lake - - - - - - - - Sky Temple Key 9
 16: Temple Grounds - - - Fortress Transport Access - - Energy Tank 3
 17: Temple Grounds - - - Profane Path  - - - - - - - - Beam Ammo Expansion 1
 18: Temple Grounds - - - Phazon Grounds  - - - - - - - Missile Expansion 9
 19: Temple Grounds - - - Ing Reliquary - - - - - - - - Sky Temple Key 7
 20: Great Temple - - - - Transport A Access  - - - - - Missile Expansion 10
 21: Great Temple - - - - Temple Sanctuary  - - - - - - Energy Transfer Module
 22: Great Temple - - - - Transport B Access  - - - - - Missile Expansion 11
 23: Great Temple - - - - Main Energy Controller  - - - Violet Translator
 24: Great Temple - - - - Main Energy Controller  - - - Light Suit
 25: Agon Wastes  - - - - Mining Plaza  - - - - - - - - Energy Tank 4
 26: Agon Wastes  - - - - Mining Station Access - - - - Energy Tank 5
 27: Agon Wastes  - - - - Mining Station B  - - - - - - Darkburst
 28: Agon Wastes  - - - - Transport Center  - - - - - - Missile Expansion 12
 29: Agon Wastes  - - - - Mining Station A  - - - - - - Missile Expansion 13
 30: Agon Wastes  - - - - Ing Cache 4 - - - - - - - - - Missile Expansion 14
 31: Agon Wastes  - - - - Junction Site - - - - - - - - Missile Expansion 15
 32: Agon Wastes  - - - - Storage A - - - - - - - - - - Missile Expansion 16
 33: Agon Wastes  - - - - Mine Shaft  - - - - - - - - - Energy Tank 6
 34: Agon Wastes  - - - - Crossroads  - - - - - - - - - Missile Expansion 17
 35: Agon Wastes  - - - - Sand Cache  - - - - - - - - - Missile Expansion 18
 36: Agon Wastes  - - - - Portal Access A - - - - - - - Missile Expansion 19
 37: Agon Wastes  - - - - Judgment Pit  - - - - - - - - Space Jump Boots
 38: Agon Wastes  - - - - Agon Temple - - - - - - - - - Morph Ball Bomb
 39: Agon Wastes  - - - - Trial Tunnel  - - - - - - - - Dark Agon Key 1
 40: Agon Wastes  - - - - Central Mining Station  - - - Beam Ammo Expansion 2
 41: Agon Wastes  - - - - Warrior's Walk  - - - - - - - Missile Expansion 20
 42: Agon Wastes  - - - - Sandcanyon  - - - - - - - - - Power Bomb Expansion 2
 43: Agon Wastes  - - - - Dark Agon Temple  - - - - - - Dark Suit
 44: Agon Wastes  - - - - Battleground  - - - - - - - - Dark Agon Key 3
 45: Agon Wastes  - - - - Battleground  - - - - - - - - Sky Temple Key 1
 46: Agon Wastes  - - - - Agon Energy Controller  - - - Amber Translator
 47: Agon Wastes  - - - - Ventilation Area A  - - - - - Missile Expansion 21
 48: Agon Wastes  - - - - Command Center  - - - - - - - Missile Expansion 22
 49: Agon Wastes  - - - - Main Reactor  - - - - - - - - Missile Expansion 23
 50: Agon Wastes  - - - - Doomed Entry  - - - - - - - - Dark Agon Key 2
 51: Agon Wastes  - - - - Sand Processing - - - - - - - Missile Expansion 24
 52: Agon Wastes  - - - - Storage D - - - - - - - - - - Dark Beam
 53: Agon Wastes  - - - - Dark Oasis  - - - - - - - - - Sky Temple Key 2
 54: Agon Wastes  - - - - Storage B - - - - - - - - - - Missile Expansion 25
 55: Agon Wastes  - - - - Feeding Pit - - - - - - - - - Power Bomb Expansion 3
 56: Agon Wastes  - - - - Bioenergy Production  - - - - Energy Tank 7
 57: Agon Wastes  - - - - Ing Cache 1 - - - - - - - - - Light Beam
 58: Agon Wastes  - - - - Storage C - - - - - - - - - - Missile Expansion 26
 59: Agon Wastes  - - - - Ing Cache 2 - - - - - - - - - Sonic Boom
 60: Torvus Bog - - - - - Torvus Lagoon - - - - - - - - Missile Expansion 27
 61: Torvus Bog - - - - - Portal Chamber  - - - - - - - Missile Expansion 28
 62: Torvus Bog - - - - - Path of Roots - - - - - - - - Missile Expansion 29
 63: Torvus Bog - - - - - Forgotten Bridge  - - - - - - Missile Expansion 30
 64: Torvus Bog - - - - - Great Bridge  - - - - - - - - Power Bomb Expansion 4
 65: Torvus Bog - - - - - Cache A - - - - - - - - - - - Beam Ammo Expansion 3
 66: Torvus Bog - - - - - Plaza Access  - - - - - - - - Missile Expansion 31
 67: Torvus Bog - - - - - Abandoned Worksite  - - - - - Missile Expansion 32
 68: Torvus Bog - - - - - Poisoned Bog  - - - - - - - - Sky Temple Key 3
 69: Torvus Bog - - - - - Venomous Pond - - - - - - - - Dark Torvus Key 3
 70: Torvus Bog - - - - - Temple Access - - - - - - - - Energy Tank 8
 71: Torvus Bog - - - - - Torvus Plaza  - - - - - - - - Energy Tank 9
 72: Torvus Bog - - - - - Putrid Alcove - - - - - - - - Power Bomb Expansion 5
 73: Torvus Bog - - - - - Torvus Grove  - - - - - - - - Missile Expansion 33
 74: Torvus Bog - - - - - Torvus Temple - - - - - - - - Super Missile
 75: Torvus Bog - - - - - Dark Torvus Arena - - - - - - Boost Ball
 76: Torvus Bog - - - - - Dark Torvus Arena - - - - - - Dark Torvus Key 1
 77: Torvus Bog - - - - - Underground Tunnel  - - - - - Missile Expansion 34
 78: Torvus Bog - - - - - Meditation Vista  - - - - - - Energy Tank 10
 79: Torvus Bog - - - - - Dark Torvus Temple  - - - - - Dark Visor
 80: Torvus Bog - - - - - Cache B - - - - - - - - - - - Energy Tank 11
 81: Torvus Bog - - - - - Hydrodynamo Station - - - - - Missile Expansion 35
 82: Torvus Bog - - - - - Torvus Energy Controller  - - Emerald Translator
 83: Torvus Bog - - - - - Undertemple Access  - - - - - Dark Torvus Key 2
 84: Torvus Bog - - - - - Gathering Hall  - - - - - - - Missile Expansion 36
 85: Torvus Bog - - - - - Training Chamber  - - - - - - Missile Expansion 37
 86: Torvus Bog - - - - - Sacrificial Chamber - - - - - Grapple Beam
 87: Torvus Bog - - - - - Undertemple - - - - - - - - - Missile Expansion 38
 88: Torvus Bog - - - - - Undertemple - - - - - - - - - Power Bomb
 89: Torvus Bog - - - - - Transit Tunnel South  - - - - Missile Expansion 39
 90: Torvus Bog - - - - - Transit Tunnel East - - - - - Energy Tank 12
 91: Torvus Bog - - - - - Dungeon - - - - - - - - - - - Sky Temple Key 4
 92: Torvus Bog - - - - - Hydrochamber Storage  - - - - Gravity Boost
 93: Torvus Bog - - - - - Undertransit One  - - - - - - Missile Expansion 40
 94: Sanctuary Fortress - Sanctuary Entrance  - - - - - Power Bomb Expansion 6
 95: Sanctuary Fortress - Reactor Core  - - - - - - - - Energy Tank 13
 96: Sanctuary Fortress - Transit Station - - - - - - - Power Bomb Expansion 7
 97: Sanctuary Fortress - Sanctuary Map Station - - - - Missile Expansion 41
 98: Sanctuary Fortress - Hall of Combat Mastery  - - - Missile Expansion 42
 99: Sanctuary Fortress - Main Research - - - - - - - - Missile Expansion 43
100: Sanctuary Fortress - Culling Chamber - - - - - - - Ing Hive Key 1
101: Sanctuary Fortress - Central Area Transport West - Missile Expansion 44
102: Sanctuary Fortress - Dynamo Works  - - - - - - - - Spider Ball
103: Sanctuary Fortress - Dynamo Works  - - - - - - - - Missile Expansion 45
104: Sanctuary Fortress - Hazing Cliff  - - - - - - - - Missile Expansion 46
105: Sanctuary Fortress - Watch Station - - - - - - - - Beam Ammo Expansion 4
106: Sanctuary Fortress - Hive Dynamo Works - - - - - - Sky Temple Key 6
107: Sanctuary Fortress - Sentinel's Path - - - - - - - Missile Expansion 47
108: Sanctuary Fortress - Watch Station Access  - - - - Energy Tank 14
109: Sanctuary Fortress - Aerial Training Site  - - - - Ing Hive Key 3
110: Sanctuary Fortress - Aerial Training Site  - - - - Missile Expansion 48
111: Sanctuary Fortress - Main Gyro Chamber - - - - - - Power Bomb Expansion 8
112: Sanctuary Fortress - Vault - - - - - - - - - - - - Screw Attack
113: Sanctuary Fortress - Temple Access - - - - - - - - Missile Expansion 49
114: Sanctuary Fortress - Hive Gyro Chamber - - - - - - Ing Hive Key 2
115: Sanctuary Fortress - Hive Temple - - - - - - - - - Annihilator Beam
116: Sanctuary Fortress - Sanctuary Energy Controller - Cobalt Translator
117: Sanctuary Fortress - Hive Entrance - - - - - - - - Sky Temple Key 5
118: Sanctuary Fortress - Aerie - - - - - - - - - - - - Echo Visor
