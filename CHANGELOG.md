# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.15.0] - 2018-10-27
- Added a timeout of 2 minutes to seed generation.
- Added two new difficulties:
  - Trivial: An expansion of No Glitches, where no tricks are used but some clever abuse of room layouts are used.
  - Hypermode: The highest difficulty tricks, mostly including ways to skip Space Jump, are now exclusive to this difficulty.
- Removed Controller Reset tricks. This trick doesn't work with Nintendon't. This will return later as an additional configuration.

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
