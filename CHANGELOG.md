# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
- Changed: "Faster credits" and "Skip item acquisitions popups" are no longer included in permalinks.  

## [0.21.0] - 2019-01-31
- **Major**: now using Claris' Randomizer version 4.0. See [Changelog](https://pastebin.com/HdK9jdps).

- Added: Randovania now changes the game id to G2ME0R, ensuring it has different saves.
- Added: Game name is now changed to 'Metroid Prime 2: Randomizer - SEEDHASH'. Seed hash is a 8 letter/number
    combination that identifies the seed being played.
- Changed: the ISO name now uses the seed hash instead of the permalink. This avoids issues with the permalink containing /
- Changed: Removed Agon Temple door lock after fighting Bomb Guardian, since this has been fixed in the Randomizer.
- Fixed: Selecting an non-existent directory for Output Directory had inconsistent results

## [0.20.2] - 2019-01-26
- Fixed: changed release zip to not use BZIP2. This fixes the native windows zip client being unable to extract. 

0.20.1 was skipped due to technical issues.

## [0.20.0] - 2019-01-13
- Added: an icon! Thanks to Dyceron for the icon.
- Added: a simple Tracker to allow knowing where you can go with a given item state
- Changed: Don't consider that Seeker Launcher give missiles for logic, so it's never
    considered a missile source.

## [0.19.1] - 2019-01-06
- Fixed: Hydrodynamo Station's Door to Training Access now correctly needs Seekers
- Added: New alternatives with tricks to get the pickup in Mining Plaza A.
- Added: Trick to cross the Mining Plaza A backwards while it's closed.
- Changed: Added a chance for Temple Keys not being always placed last.
- Changed: Light Suit now has a decreased chance of being placed early.

0.19.0 was skipped due to technical issues.

## [0.18.0] - 2019-01-02
- Added: Editor for Randovania's database. This allows for modifications and contributions to be made easily.
    There's currently no way to use the modified database directly.
- Added: Options to place the Sky Temple Keys on Guardians + Sub-Guardians or just on Guardians.
- Changed: Removed Space Jump method from Training Chamber.
- Changed: Added Power Bomb as option for pickup in Hive Chamber B.
- Changed: Shortened Permalinks when pickup quantities aren't customized.
- Added: Permalinks now include the database version they were created for.
- Fixed: Logic mistake in item distribution that made some impossible seeds.
- Changed: For now, don't consider Chykka a "can only do once" event, since Floaty is not used.
- Fixed: Permalinks now properly ignore the Energy Transfer Module.   

## [0.17.2] - 2018-12-27
- Fixed: 'Clear loaded game' now properly does it's job.
- Changed: Add an error message to capture potential Randomizer failures.
- Changed: Improved README.

## [0.17.1] - 2018-12-24
- Fixed: stray tooltips in GUI elements were removed.
- Fixed: multiple typos in GUI elements.

## [0.17.0] - 2018-12-23
- New: Reorganized GUI!
  - Seed Details and Data Visualizer are now different windows opened via the menu bar.
  - There are now three tabs: ROM Settings, Logic Settings and Item Quantities.
- New: Option to disable generating an spoiler.
- New: All options can now be exported and imported via a permalink. 
- Changed: Renamed "Logic" to "Trick Level" and "No Glitches" to "No Tricks". Appropriate labels in the GUI and files
changed to match.
- Internal: no longer using the py.path and dataset libraries

## [0.16.2] - 2018-12-01
- Fixed: adding multiples of an item now works properly.

## [0.16.1] - 2018-11-25
- Fixed: pressing the Reset button in the Item Quantity works properly.
- Fixed: hiding help in Layout Generation will no longer hide the item names in Item Quantity.

## [0.16.0] - 2018-11-20
- Updated item distribution: seeds are now less likely to have all items in the beginning, and some items less likely to appear in vanilla locations.
- Item Mode (Standard/Major Items) removed for now.

## [0.15.0] - 2018-10-27
- Added a timeout of 2 minutes to seed generation.
- Added two new difficulties:
  - Trivial: An expansion of No Glitches, where no tricks are used but some clever abuse of room layouts are used.
  - Hypermode: The highest difficulty tricks, mostly including ways to skip Space Jump, are now exclusive to this difficulty.
- Removed Controller Reset tricks. This trick doesn't work with Nintendont. This will return later as an additional configuration.

## [0.14.0] - 2018-10-07
- **Major**: Added support for randomizing elevators. 
- Fixed spin boxes for item quantities changing while user scrolled the window.
It is now needed to click on them before using the mouse wheel to change their values.
- Fixed some texts being truncated in the Layout Generation window.
- Fixed generation failing when adding multiple of some items.
- Added links to where to find the Menu Mod.
- Changed the order of some fields in the Seed Log.  

## [0.13.2] - 2018-06-28
- Fixed logic missing Amber Translator being required to pass by Path of Eyes.

## [0.13.1] - 2018-06-27
- Fixed logic errors due to inability to reload Main Reactor after defeating Dark Samus 1.
- Added prefix when loading resources based on type, improving logs and Data Visualizer.

## [0.13.0] - 2018-06-26
- Added new logic: "Minimal Validation". This logic only checks if Dark Visor, Light Suit and Screw Attack won't lock each other.
- Added option to include the Claris' Menu Mod to the ISO.
- Added option to control how many of each item is added to the game.

## [0.12.0] - 2018-09-23
- Improved GUI usability
- Fixed Workers Path not requiring Cobalt Translator to enter

## [0.11.0] - 2018-07-30
- Randovania should no longe create invalid ISOs when the game files are bigger than the maximum ISO size: an error is properly reported in that case.
- When exporting a Metroid Prime 2: Echoes ISO if the maximum size is reached there's is now an automatic attempt to fix the issue by running Claris' "Disable Echoes Attract Videos" tool from the Menu Mod.
- The layout log is automatically added to the game's files when randomizing.
- Simplified ISO patching: by default, Randovania now asks for an input ISO and an output path and does everything else automatically.

## [0.10.0] - 2018-07-15
- This release includes the capability to generate layouts from scratch and these to the game, skipping the entire searching step!

## [0.9.2] - 2018-07-10
- Added: After killing Bomb Guardian, collecting the pickup from Agon Energy Controller is necessary to unlock the Agon Temple door to Temple Access.
- Added a version check. Once a day, the application will check GitHub if there's a new version.
- Preview feature: option to create item layouts, instead of searching for seeds. This is much more CPU friendly and faster than searching for seeds, but is currently experimental: generation is prone to errors and items concentrated in early locations. To use, open with randovania.exe gui --preview from a terminal. Even though there are many configuration options, only the Item Loss makes any difference.


## [0.9.1] - 2018-07-21
- Fixed the Ing Cache in Accursed Lake didn't need Dark Visor.

## [0.9.0] - 2018-05-31
- Added a fully featured GUI.

## [0.8.2] - 2017-10-19
- Stupid mistake.

## [0.8.1] - 2017-10-19
- Fix previous release.

## [0.8.0] - 2017-10-19
- Save preferences.
- Added Claris Randomizer to the binary release.

## [0.7.1] - 2017-10-17
- Fixed the interactive .bat

## [0.7.0] - 2017-10-14
- Added an interactive shell.
- Releases now include the README.

## [0.5.0] - 2017-10-10
- Releases now include standalone windows binaries
