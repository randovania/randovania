# randovania
A randomizer validator for the Metroid Prime series.

### Installation

With a Python 3.6 installation:

`python3 -m pip install randovania`
 
### Usage

`python3 -m randovania echoes validate path/to/randomizer.log`

Checks if the given [Metroid Prime 2: Echoes Randomizer](
https://m2k2.taigaforum.com/post/echoes_randomizer.html) seed is beatable
by a casual player.

`python3 -m randovania echoes validate --difficulty 5
--enable-tricks --skip-item-loss path/to/randomizer.log`

Check if the seed if the given seed is beatable using every known trick,
no matter how difficult. This does not include going out of bounds.

### Limitations

* Item Loss is not properly implemented. If --skip-item-loss, the
validator assumes you start with missiles and bombs.
* There's no way to choose each trick individually.
* There's no way to print more details of which route the validator
used to finish the game.
* The data set does not include out of bounds movement.

### Options

See `python3 -m randovania --help`.


### Credits

Many thanks to [Claris Robyn](https://www.twitch.tv/clarisrobyn) for
making the Echoes Randomizer and both collecting and providing this
incredible set of data which powers this validator.
