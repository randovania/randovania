# Glossary

Index of terminology used in Randovania. Certain terms sometimes are used only in the GUI, with more technical ones being used in code or CLI.

## Area
## Database
## Event
## Game Patches

## Generator

The part of Randovania that takes the database, the preset settings, a random number generator and decides which pickups should be placed where, as well as everything else that is randomly decided in the layout.

## Hint
## Item

A kind of resource that represents something a player has during the game.

Examples:
- Space Jump Boots in Metroid Prime 1/2.
- Missiles in Metroid games.

## Layout

Internal name for the output of the generator. Contains all modifications (GamePatches) for all players, along with a permalink.

The GUI uses "randomized game", "generated game" or something similar instead.

Whenever plandomizers are supported, they'd be a hand-made layout.

## Log File

Colloquial term for a LayoutDescription serialized to a file.

## Logic

Colloquial term for how a randomizer works. Can mean one of:
* Most often, the rules that govern what you need to reach certain in-game location. See Database and Requirement.
* Predicting pickup placement based on the generator tells.

## Multiworld

## Node

## Patcher

The code responsible for making the actual game modifications.

## Permalink

String with all data necessary to generate a game/LayoutDescription. Support for permalinks are only guaranteed if using the same specific version, or when using stable releases, the same major.minor series.

For code: Contains one 32-bit int and one preset for each player.

## Pickup

Represents something that can be collected. Gives a quantity of any number of items. Can also be progressive, giving some item based on which items the player has.
When starting the generator, a pool of pickups is created based on the preset.

## Pickup Location / Pickup Node

Represents a place the in the game map where a pickup can be found. All locations will be assigned a pickup during the generation.

## Preset

Versioned object with all generation settings for one given game. Can be exported to a file and shared. Randovania supports presets from older versions automatically.

## Requirement

Describes what kinds of resources are required in order to do something.
Used by the database to connect different nodes in a way that can be used by the generator.

## Resource

Some in-game concept that the generator or solver must have in order to solve requirements.

See Items, Events, Tricks for examples.

## RNG

Acronym for "Random Number Generator". Commonly used in speedrunning communities as an alias to random/randomness.
This term is not used at all in the GUI and in the code only to describe an object of type `random.Random`.

## Seed

Commonly used to refer to a layout.

Internally, this is used only to refer to the value used to initialize a random number generator.

## Solver

The part of Randovania that takes a layout and determines a path that can reach the victory condition.

By default runs for all one-player layouts after generation.

## Trick

A resource that represents some non-trivial gameplay, usually by exploiting some mechanic or glitch.

Examples:
- Slope Jumps in the Metroid Primes.

## World

TODO