# randovania
A randomizer validator for the Metroid Prime series.

### Installation

With a Python 3.6 installation:

`python3 -m pip install --upgrade randovania`
 
### Usage

`python3 -m randovania echoes validate path/to/randomizer.log`

Checks if the given [Metroid Prime 2: Echoes Randomizer](
https://m2k2.taigaforum.com/post/echoes_randomizer.html) seed is beatable
by a casual player.

`python3 -m randovania echoes validate --difficulty 5
--enable-tricks --skip-item-loss --print-final-path path/to/randomizer.log`

Check if the seed if the given seed is beatable using every known trick,
no matter how difficult. This does not include going out of bounds.

It will also print the order of pickups taken and events triggered in
order to finish the game.

`python3 -m randovania echoes randomize --randomizer-binary
D:\Randomizer\Randomizer.exe --remove-hud-memo-popup --enable-tricks
--difficulty 3 --skip-item-loss D:\MetroidPrime2-Rando\files`

Generate a new seed and validate it until a possible seed is found.

### Limitations

* There's no way to choose each trick individually.
* The data set does not include out of bounds movement.
* Dark World damage requirements, while mapped, are not verified.
* Elevator randomizer is not supported.

### Options

See `python3 -m randovania --help`.


### Credits

Many thanks to [Claris Robyn](https://www.twitch.tv/clarisrobyn) for
making the Echoes Randomizer and both collecting and providing this
incredible set of data which powers this validator.
