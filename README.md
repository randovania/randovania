# Randovania

With Randovania, each Metroid Prime 2: Echoes playthrough shuffles the location of all items in the game.
You could find the Light Beam right off the start, or the Bombs deep inside Sanctuary Fortress.

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

* [Python 3.7 64-bit](https://www.python.org/downloads/release/python-376/)
* [Git](https://git-scm.com/downloads)

### Setup

1. Clone this repository
2. Open a terminal in the repository root
3. Create a virtual environment: `py -3.7 -m venv venv`
4. Activate the virtual environment `venv\scripts\activate`
5. Install pip/setuptools: `python -m pip install --upgrade -r requirements-setuptools.txt`
6. Install requirements: `python -m pip install --upgrade -r requirements.txt`
7. Generate the UI files: `python setup.py build_ui`
7. Install Randovania as editable: `python -m pip install -e .`
8. Run with `python -m randovania`

Suggested IDE: [PyCharm Community](https://www.jetbrains.com/pycharm/download/)

### Third Party packages

Our requirements.txt is kept up to do date with help from PyUp.io, which automatically opens
pull requests to update when new releases are made.
