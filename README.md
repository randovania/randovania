# Randovania

With Randovania, each Metroid Prime 2: Echoes playthrough shuffles the location of all items in the game.
You could find the Light Beam right off the start, or the Bombs deep inside Sanctuary Fortress.

## Installation

### Windows

In the [releases page](https://github.com/henriquegemignani/randovania/releases), we have zip files
with everything ready to use. Just extract and run!

## Community

Join the Metroid Prime Randomizer Discord: <https://discord.gg/gymstUz>

## Credits
Game patching written by [Claris](https://www.twitch.tv/claris).

GUI and logic written by [Henrique Gemignani](https://github.com/henriquegemignani/), with some
contributions by [SpaghettiToastBook](https://www.twitch.tv/spaghettitoastbook).

Many thanks to [Claris](https://www.twitch.tv/claris) for
making the Echoes Randomizer and both collecting and providing this
incredible set of data which powers Randovania.

Claris also made the included [Menu Mod](https://www.dropbox.com/s/yhqqafaxfo3l4vn/Echoes%20Menu.7z),
a tool for practicing Echoes. For more information, see the
[Menu Mod README](https://www.dropbox.com/s/yhqqafaxfo3l4vn/Echoes%20Menu.7z?file_subpath=%2FEchoes+Menu%2Freadme.txt).

Also thanks to [Dyceron](https://www.twitch.tv/dyceron) for motivation and testing.

## Developer Help

### Dependencies

* [Python 3.7 64-bit](https://www.python.org/downloads/release/python-376/)
* [Git](https://git-scm.com/downloads)

### Setup

1.  Clone the git repository: `git clone https://github.com/randovania/randovania/`
2.  With a terminal in the repository root:
    1. Install pip/setuptools: `python -m pip install --upgrade -r requirements-setuptools.txt`
    2. Install requirements:   `python -m pip install --upgrade -r requirements.txt`
    3. Install Randovania as editable: `python -m pip install -e .`
3.  Run with `python -m randovania`

Suggested IDE: [PyCharm Community](https://www.jetbrains.com/pycharm/download/)
