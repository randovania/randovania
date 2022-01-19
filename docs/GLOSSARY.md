# Glossary

Index of terminology used in Randovania. Certain terms sometimes are used only in the GUI, with more technical ones being used in code or CLI.

## Area

TODO

## Configuration

TODO

## Dangerous Action

TODO

## Database

TODO

## Event

TODO

## Game Patches

TODO

## Generator

The part of Randovania that takes the [database](#database), the [preset](#preset) settings, a [random number generator](#rng) and decides which [pickups](#pickup) should be placed where, as well as everything else that is randomly decided in the [layout](#layout).

## Hint

TODO

## Item

A kind of [resource](#resource) that represents something a player has during the game.

Examples:
- Space Jump Boots in Metroid Prime 1/2.
- Missiles in Metroid games.

## Item Check

Colloquial term for a [pickup node](#pickup-location-/-pickup-node), e.g. "Phazon Suit only opens up one check."

## Layout

Internal name for the output of the [generator](#generator). Contains all modifications ([GamePatches](#game-patches)) for all players, along with a [permalink](#permalink).

The GUI uses "randomized game", "generated game" or something similar instead.

Whenever [plandomizers](#plandomizer) are supported, they'd be a hand-made layout.

## Log File

Colloquial term for a [LayoutDescription](#layout) serialized to a .rdvgame file.

## Logic

Colloquial term for how a randomizer works. Can mean one of:
- Most often, the rules that govern what you need to reach certain in-game location. See [Database](#database) and [Requirement](#requirement).
- Predicting [pickup](#pickup) placement based on the [generator](#generator) tells.

## Multiworld

A multiplayer randomizer session in which the [pickup](#pickup) pool for each player is shuffled together as a single pool, with pickups for any player being placed in a given player's [layout](#layout). Each player will have a unique layout, and the required [progression](#progression) will often jump back and forth between players.

## Node

TODO

## Patcher

The code responsible for making the actual game modifications, generally according to the results of [GamePatches](#game-patches).

## Permalink

String with all data necessary to generate a game/[LayoutDescription](#layout). Support for permalinks are only guaranteed if using the same specific version, or when using stable releases, the same major.minor series.

For code: Contains one 32-bit int and one [preset](#preset) for each player.

## Pickup

Represents something that can be collected. Gives a quantity of any number of [items](#item). Can also be progressive, giving some item based on which items the player has.
When starting the [generator](#generator), a pool of pickups is created based on the [preset](#preset).

## Pickup Location / Pickup Node

Represents a place the in the game map where a [pickup](#pickup) can be found. All locations will be assigned a pickup during the generation.

## Plandomizer

TODO

## Point of no Return

A point of no return (PONR) is a colloquial term for a [dangerous action](#dangerous-action). It is sometimes used to more specifically refer to dangerous actions involving travelling from one [node](#node) to another, not including actions such as collecting [events](#event) or [pickups](#pickup) which are otherwise dangerous.

## Preset

Versioned object with all generation settings (the [Configuration](#configuration)) for one given game. Can be exported to a .rdvpreset file and shared. Randovania supports presets from older versions automatically.

## Progression

TODO

## Requirement

Describes what kinds of [resources](#resource) are required in order to do something.
Used by the [database](#database) to connect different [nodes](#node) in a way that can be used by the [generator](#generator).

## Resource

Some in-game concept that the [generator](#generator) or [solver](#solver) must have in order to solve [requirements](#requirement).

See [Items](#item), [Events](#event), [Tricks](#trick) for examples.

## RNG

Acronym for "Random Number Generator". Commonly used in speedrunning communities as an alias to random/randomness.
This term is not used at all in the GUI and in the code only to describe an object of type `random.Random`.

## Seed

Commonly used to refer to a [layout](#layout).

Internally, this is used only to refer to the value used to initialize a [random number generator](#rng).

## Solver

The part of Randovania that takes a [layout](#layout) and determines a path that can reach the [victory condition](#layout).

By default runs for all single-player layouts after generation.

## Trick

A [resource](#resource) that represents some non-trivial gameplay, usually by exploiting some mechanic or glitch.

Examples:
- Slope Jumps in the Metroid Primes.

## Victory Condition

A single [requirement](#requirement) defined for each game in order to determine whether the game's objective can be completed.

Examples:
- Reaching the Credits room in the Metroid Primes
- Achieving any of the three endings in Cave Story

## World

TODO
