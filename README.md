<!-- The Begin and End comments throughout this document are used in order to pull specific sections of the readme into the main GUI window at runtime. -->

# Randovania

Welcome to Randovania, a randomizer platform for a multitude of games.

<!-- Begin SUPPORTED -->

### Supported Games
 - Metroid Prime
 - Metroid Prime 2: Echoes
 - Cave Story

<!-- End SUPPORTED -->

<!-- Begin EXPERIMENTAL -->

### Experimental Games
 - Metroid Prime 3: Corruption
 - Metroid Dread
 - Super Metroid

<!-- End EXPERIMENTAL -->

<!-- Begin WELCOME -->

Here you will be able to randomize many aspects of either game, while still being ensured it's possible to 
finish without any trick or glitch! What can be randomized?

* Randomize what can be found in each pickup location, including major upgrades, expansions, keys and artifacts.

* Play with multiple people, via multiworld sessions. Your pickups will be shuffled among the games of
everyone involved, no matter what game they're playing!

* Randomize where each teleporter goes, or what you need to unlock a translator gate. In either case, 
there's advanced options for how they're shuffled.

* The location you start the game in as well as the items you start with. If you're feeling brave, 
you can even shuffle items you normally start with, like the Power Beam and Scan Visor.

So have fun and start randomizing.

<!-- End WELCOME -->

# Installation

## Windows

In the [releases page](https://github.com/randovania/randovania/releases), we have zip files
with everything ready to use. Just extract and run!

## Linux

### Running (in-source)

1. Clone this repository (downloading the source zip is not supported and will not work)
2. Open a terminal in the repository root
3. Fetch the tags from the repo:

   `$ git fetch --tags`
4. Checkout the latest tag (replace v4.0.1 with the latest release version):

   `$ git checkout v4.0.1`
5. Prepare the virtual environment and install dependencies:
   
   `$ tools/prepare_virtual_env.sh`
6. Run the program from source:

   `$ tools/start_client.sh`

### Running Natively and Multiworld

1. Activate the virtual environment and generate the necessary configuration.json, as well as build a native application:

   ```console
   $ . venv/bin/activate
   (venv) $ export PRODUCTION=true
   (venv) $ python tools/create_release.py
   ```
2. Navigate into the build/randovania directory
3. Install the generated randovania.pkg or run the generated executable

<!-- Begin COMMUNITY -->

# Community

Join the Randovania Discord: <https://discord.gg/M23gCxj6fw>

Invite links for specific games' servers can be found in the `#game-communities` channel in our server.

<!-- End COMMUNITY -->

<!-- Begin CREDITS -->

# Credits

GUI and logic written by [Henrique Gemignani](https://github.com/henriquegemignani/), with contributions 
by [SpaghettiToastBook](https://www.twitch.tv/spaghettitoastbook), [gollop](https://github.com/gollop) and [many others](https://github.com/randovania/randovania/graphs/contributors).

[BashPrime](https://www.twitch.tv/bashprime), [Pwootage](https://github.com/Pwootage), and [April Wade](https://github.com/aprilwade) made <https://randomizer.metroidprime.run/>, from which the GUI was based.

## Games

### Metroid Prime 1
* Game patching via [randomprime](https://github.com/aprilwade/randomprime) from April Wade, with contributions from [UltiNaruto](https://github.com/UltiNaruto), BashPrime and toasterparty.
* Room data collected by UltiNaruto, [EthanArmbrust](https://github.com/EthanArmbrust) and [SolventMercury](https://github.com/SolventMercury).

### Metroid Prime 2: Echoes
* Game patching written by [Claris](https://www.twitch.tv/claris).
* Room data initially collected by Claris, revamped by [Dyceron](https://www.twitch.tv/dyceron).
* [Menu Mod](https://www.dropbox.com/s/yhqqafaxfo3l4vn/Echoes%20Menu.7z) created by Claris. For more information, see the
[Menu Mod README](https://www.dropbox.com/s/yhqqafaxfo3l4vn/Echoes%20Menu.7z?file_subpath=%2FEchoes+Menu%2Freadme.txt).

### Metroid Prime 3: Corruption
* Game patching written by [gollop](https://github.com/gollop).
* Room data collected by [Dyceron](https://www.twitch.tv/dyceron) and [KirbymastaH](https://www.twitch.tv/kirbymastah).

### Super Metroid
* Game Patching and Logic Database by [SolventMercury](https://github.com/SolventMercury).
* Custom Item PLMs patch by [Kazuto](https://github.com/Kazuto88).
* Skip Intro Saves patch by [PHOSPHOTiDYL](https://metroidconstruction.com/resource.php?id=265).
* Other individual patches by [Total](https://github.com/tewtal), Foosda, Leodox, and others.

### Cave Story
* Patcher and logic written by [duncathan_salt](https://twitter.com/duncathan_salt).
* Based on the [original randomizer](https://shru.itch.io/cave-story-randomizer) by shru.
* Features contributions from [many others](https://github.com/cave-story-randomizer/cave-story-randomizer/graphs/contributors).

### Metroid Dread
* Game Patching by [Henrique Gemignani](https://github.com/henriquegemignani/) and [duncathan_salt](https://twitter.com/duncathan_salt).
* Room data initially collected by [KirbymastaH](https://www.twitch.tv/kirbymastah) (connections), [Dyceron](https://www.twitch.tv/dyceron) (area names) and Henrique Gemignani (initial structure).
* Morph Ball and Speed Booster pickup textures created by [BigSharkZ](https://www.youtube.com/BigSharkZ). Spider Magnet pickup texture by duncathan_salt with help from BigSharkZ. 

## Auto Tracker
Game theme assets were provided by [MaskedTAS](https://twitter.com/MaskedKirby).

## Multiworld
Server and logic written by Henrique, including Dolphin and Nintendont integrations. These were based on [Dolphin Memory Engine](https://github.com/aldelaro5/Dolphin-memory-engine) and Pwootage's Nintendont fork, respectively. In-game message alert initially written by [encounter](https://github.com/encounter).

<!-- End CREDITS -->

# Developer Help

## Dependencies

* [Python 3.9 64-bit](https://www.python.org/ftp/python/3.9.10/python-3.9.10-amd64.exe)
* [Git](https://git-scm.com/downloads)

## Setup

Getting started:
   1. Clone this repository (downloading the zip is *not* supported and will not work)
   2. Open a terminal in the repository root
   3. Run the following file:
      1. Windows: `tools/prepare_virtual_env.bat`
      2. Linux/macOS: `tools/prepare_virtual_env.sh`
   4. You should see "Setup finished successfully." visible when the command finishes.

In order to start Randovania, open:
   1. Windows: `tools/start_client.bat`
   2. Linux/macOS: `tools/start_client.sh` 

In order to update your repository:
   1. Update the git repository. (With `git pull` or anything else)
   2. Make sure that Randovania is closed.
   3. Re-run the steps from "Getting Started", starting at step 2.
      1. In case of unexpected errors, delete the `venv` in the root of the repository and start again.
   4. Open Randovania normally.

In order to run the tests:
   1. Run both "Getting started" and "Start Randovania" steps. 
   2. Activate the virtual env. Check start_client.bat/sh for details.
   3. Run `python -m pip install -r requirements.txt`.
   4. Run `python -m pytest test`.

In order to run the server:
   1. Run both "Getting started" and "Start Randovania" steps. 
   2. Activate the virtual env. Check start_client.bat/sh for details.
   3. Run `python -m pip install -r requirements.txt`.
   4. Run `python tools/prepare_dev_server_config.py` once.
   5. If you wish to use any Discord functionality, you'll need to create an app in Discord 
   and fill both ids in `tools/dev-server-configuration.json`.  
   6. Run the server with `tools/start_dev_server.bat` and the client with `tools/start_debug_client.bat`.

Suggested IDE: [PyCharm Community](https://www.jetbrains.com/pycharm/download/)

# Documentation

- Unfamiliar with a term? Check the [glossary](docs/GLOSSARY.md).
- Adding a new game? Check the [dedicated guide](docs/NEW_GAME.md).
- Changing a data format? Check the [migrations documentation](docs/MIGRATIONS.md).
- Working with the logic database? Check the [guide](https://github.com/SolventMercury/randovania/blob/main/docs/DATABASE_FORMAT.md).
