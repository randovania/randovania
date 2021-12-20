# Randovania

Welcome to Randovania, a randomizer for Metroid Prime and Metroid Prime 2: Echoes.

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

## Installation

### Windows

In the [releases page](https://github.com/randovania/randovania/releases), we have zip files
with everything ready to use. Just extract and run!

## Community

Join the Metroid Prime Randomizer Discord: <https://discord.gg/metroid-prime-randomizer>

## Credits
Game patching written by [Claris](https://www.twitch.tv/claris).

GUI and logic written by [Henrique Gemignani](https://github.com/henriquegemignani/), with contributions 
by [SpaghettiToastBook](https://www.twitch.tv/spaghettitoastbook) and [gollop](https://github.com/gollop).

Many thanks to Claris for making the original Echoes Randomizer and both collecting and providing this
incredible initial set of data which powers Randovania.

Claris also made the included [Menu Mod](https://www.dropbox.com/s/yhqqafaxfo3l4vn/Echoes%20Menu.7z),
a tool for practicing Echoes. For more information, see the
[Menu Mod README](https://www.dropbox.com/s/yhqqafaxfo3l4vn/Echoes%20Menu.7z?file_subpath=%2FEchoes+Menu%2Freadme.txt).

Also thanks to [Dyceron](https://www.twitch.tv/dyceron) for motivation and testing.

## Developer Help

### Dependencies

* [Python 3.9 64-bit](https://www.python.org/ftp/python/3.9.5/python-3.9.5-amd64.exe)
* [Git](https://git-scm.com/downloads)

### Setup

Getting started:
   1. Clone this repository
   2. Open a terminal in the repository root
   3. Run the following file:
      1. Windows: `tools/prepare_virtual_env.bat`
      2. Linux/macOS: `tools/prepare_virtual_env.sh`
   4. You should see "Setup finished successfully." visible when the command finishes.

In order to start Randovania, open:
   1. Windows: `tools/start_client.bat`
   2. Linux/macOS: `tools/start_client.sh` 

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

- Adding a new game? Check the [dedicated guide](docs/NEW_GAME.md).
- Changing a data format? Check the [migrations documentation](docs/MIGRATIONS.md).
