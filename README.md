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

Join the Metroid Prime Randomizer Discord: <https://discord.gg/gymstUz>

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

1. Clone this repository
2. Open a terminal in the repository root
3. Create a virtual environment: `py -3.9 -m venv venv`
4. Activate the virtual environment `venv\scripts\activate`
5. Install pip/setuptools: `python -m pip install --upgrade -r requirements-setuptools.txt`
6. Install requirements: `python -m pip install --upgrade -r requirements-small.txt`
7. Generate the UI files: `python setup.py build_ui`
7. Install Randovania as editable: `python -m pip install -e .`
8. Run with `python -m randovania`

Alternatively, install requirements.txt to run tests or server.
Suggested IDE: [PyCharm Community](https://www.jetbrains.com/pycharm/download/)
