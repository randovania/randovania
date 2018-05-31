# randovania
A randomizer validator for the Metroid Prime series.

## Installation

### Windows

Check the [releases page](https://github.com/henriquegemignani/randovania/releases).

Please note that all binary releases will be for 64-bit Windows only.

### Python Package
With a Python 3.6 installation:

`python3 -m pip install --upgrade randovania`
 
## Command Line Usage

`randovania echoes validate path/to/randomizer.log`

Checks if the given [Metroid Prime 2: Echoes Randomizer](
https://m2k2.taigaforum.com/post/randomizer_release.html) seed is beatable
by a casual player.

`randovania echoes validate --difficulty 5 --skip-item-loss
--print-final-path path/to/randomizer.log`

Check if the seed if the given seed is beatable using every known trick,
no matter how difficult. This does not include going out of bounds.

It will also print the order of pickups taken and events triggered in
order to finish the game.

`randovania echoes generate-seed --difficulty 3 --skip-item-loss`

Generate a new seed and validate it until a possible seed is found. Please
not that this is a very CPU intensive operation, and your computer can be
non-responsive while it runs.

Dropping the difficulty, or disabling `--skip-item-loss` may cause this
operation to take even hours to finish, depending on your CPU.

When finished, it will output the seed number. Use this number with the
Echoes Randomizer as usual. Be sure to remember to pass the correct 
exclusion list. (The default for this operation is _no_ exclusions.)

## Limitations

* There's no way to choose each trick individually via CLI.
* The data set does not include out of bounds movement.
* Dark World damage requirements, while mapped, are not verified.
* Opening Blast Shield doors from a side does not consider the other side
as unlocked.

## Options

See `randovania --help`.


## Credits

Many thanks to [Claris](https://www.twitch.tv/claris) for
making the Echoes Randomizer and both collecting and providing this
incredible set of data which powers this validator.
