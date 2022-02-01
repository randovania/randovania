# Glossary

Index of terminology used in Randovania. Some terms are used only in the GUI, with more technical ones being used in code or CLI.

## Area

A small chunk of a game's playable space, often only a single room. May contain one or more [Nodes](#node).

Examples:
- Phazon Mining Tunnel in Metroid Prime
- Big Pink in Super Metroid

## Configuration

A colloquial term referring to the many types of settings a player may use when generating a game. This includes trick settings, item pool settings, starting items and location, [Gameplay and Cosmetic Patches](#game-patches), and many other things.

## Dangerous Action

Any action that the [Solver](#solver) might take which it might not be able to backtrack from; a one-way action. See also [Point of No Return](#point-of-no-return).

## Database

The collection of data that represents a game's [Logic](#logic), including the layout of [Worlds](#world) and [Areas](#area), the [Resources](#resource) a player has to progress, the locations of [Pickups](#pickup) and spawn points, and other information.

## Event

A logical [Resource](#resource) representing an event that may be triggered in game. Events can only be completed once, and cannot be undone.

## Game Patches

A modification made to the game. Usually refers to specific changes made to the game, such as cutscene alterations, and not to the randomization process itself.

## Generator

The part of Randovania that takes the [Database](#database), the [Preset](#preset) settings, a [Random Number Generator](#rng) and decides which [Pickups](#pickup) should be placed where, as well as everything else that is randomly decided in the [Layout](#layout).

## Hint

A piece of text placed in the game world which may give the player information about how [Pickups](#pickup) were placed. This is distinct from [Log Files](#log-file), which contain all details of a generated game, and are generally considered to be a form of cheating in most competitive settings.

## Item

A kind of [Resource](#resource) that represents something a player has during the game.

Examples:
- Space Jump Boots in Metroid Prime 1/2.
- Missiles in Metroid games.

## Item Pool

The available pool of items that can be placed as pickups during generation, and rules governing how they should be placed. Also includes information about [Starting Items](#starting-items).

## Item Check

Colloquial term for a [Pickup Node](#pickup-location-/-pickup-node), e.g. "Phazon Suit only opens up one check."

## Layout

Internal name for the output of the [Generator](#generator). Contains all modifications ([GamePatches](#game-patches)) for all players, along with a [Permalink](#permalink).

The GUI uses "randomized game", "generated game" or something similar instead.

Whenever [Plandomizers](#plandomizer) are supported, they'd be a hand-made layout.

## Log File

Colloquial term for a [LayoutDescription](#layout) serialized to a .rdvgame file. Also referred to as a Spoiler Log.

## Logic

Colloquial term for how a randomizer works. Can mean one of:
- Most often, the rules that govern what you need to reach certain in-game location. See [Database](#database) and [Requirement](#requirement).
- Predicting [Pickup](#pickup) placement based on the [Generator](#generator) tells.

## Multiworld

A multiplayer randomizer session in which the [Pickup](#pickup) pool for each player is shuffled together as a single pool, with pickups for any player being placed in a given player's [Layout](#layout). Each player will have a unique layout, and the required [Progression](#progression) will often jump back and forth between players.

## Node

Represents the smallest discrete region of playable game space, often only a single in-game object, like a door or a pickup.

## Patcher

The code responsible for making the actual game modifications, generally according to the results of [GamePatches](#game-patches).

## Permalink

String with all data necessary to generate a game/[LayoutDescription](#layout). Support for permalinks are only guaranteed if using the same specific version, or when using stable releases, the same major.minor series.

For code: Contains one 32-bit int and one [Preset](#preset) for each player.

## Pickup

Represents something that can be collected. Gives a quantity of any number of [Items](#item). Can also be progressive, giving some item based on which items the player has.
When starting the [Generator](#generator), a pool of pickups is created based on the [Preset](#preset).

## Pickup Location / Pickup Node

Represents a place the in the game map where a [Pickup](#pickup) can be found. All locations will be assigned a pickup during the generation.

## Plandomizer

A game where generation has been performed by hand, rather than by using the randomizer.

## Point of No Return

A point of no return (PONR) is a colloquial term for a [Dangerous Action](#dangerous-action). It is sometimes used to more specifically refer to dangerous actions involving travelling from one [Node](#node) to another, not including actions such as collecting [Events](#event) or [Pickups](#pickup) which are otherwise dangerous.

## Preset

Versioned object with all generation settings (the [Configuration](#configuration)) for one given game. Can be exported to a .rdvpreset file and shared. Randovania supports presets from older versions automatically.

## Progression

Anything which allows a player to access more of the game than they were previously able to.

## Requirement

Describes what kinds of [Resources](#resource) are required in order to do something.
Used by the [Database](#database) to connect different [Nodes](#node) in a way that can be used by the [Generator](#generator).

## Resource

Some in-game construct that the [Generator](#generator) or [Solver](#solver) must have in order to pass [Requirements](#requirement).

See [Items](#item), [Events](#event), and [Tricks](#trick) for examples.

## RNG

Acronym for "Random Number Generator". Commonly used in speedrunning communities as an alias to random/randomness.
This term is not used at all in the GUI and in the code only to describe an object of type `random.Random`.

## Seed

Commonly used to refer to a [Layout](#layout).

Internally, this is used only to refer to the value used to initialize a [Random Number Generator](#rng).

## Solver

The part of Randovania that takes a [Layout](#layout) and determines a path that can reach the [Victory Condition](#layout).

By default runs for all single-player layouts after generation.

## Starting Items

[Items](#item) which a player is granted immediately upon starting the game.

## Trick

A [Resource](#resource) that represents some non-trivial gameplay feat, usually by exploiting some mechanic or glitch.

Examples:
- Slope Jumps in the Metroid Primes.

## Trivial

A [Logical Requirement](#requirement) which is always considered possible to meet, regardless of the player's current [Resources](#resource).

## Victory Condition

A single [Requirement](#requirement) defined for each game in order to determine whether the game's objective can be completed.

Examples:
- Reaching the Credits room in the Metroid Primes
- Achieving any of the three endings in Cave Story

## World

The largest subdivision used when mapping a game in Randovania. Worlds contain many [Areas](#area), and there are usually only a few worlds per game.

Examples:
- Chozo Ruins in Metroid Prime
- Maridia in Super Metroid
