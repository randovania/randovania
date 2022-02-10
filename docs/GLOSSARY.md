# Glossary

Index of terminology used in Randovania. Some terms are used only in the GUI, with more technical ones being used in code or CLI.

## Action

Actions are steps taken by the generator. Consist of either assigning [Pickups](#pickup) or collecting any unsafe Resource Node.

## Area

A small chunk of a game's playable space, often only a single room. May contain one or more [Nodes](#node).

Examples:
- Phazon Mining Tunnel in Metroid Prime
- Big Pink in Super Metroid

## Burger King / BK

A strictly informal term used to describe the situation of being unable to progress in a [Multiworld](#multiworld) [Session](#session). This occurs when a player has exhausted all readily available [Checks](#item-check) and must wait for another player to send them [Progression](#progression) before they can continue. The term was coined after a player in this state left to get food from the eponymous restaurant and had yet to obtain Progression by the time they returned.

In Logical BK, a player may technically be able to perform more Checks, but none will be expected of them from the game's Logic.

In Full BK, there is absolutely no way for the player to progress on their own, and they are forced to wait until another player finds their Progression before they can continue.

## Configuration

Has two meanings:

- Colloquially, a term referring to the many types of settings a player may use when generating a game. This includes trick settings, [Pickup Pool](#pickup-pool) settings, starting items and location, [Gameplay and Cosmetic Patches](#game-patches), and many other things.

- In code, the Configuration class that each game must provide, derived from the BaseConfiguration class. This is where game-specific parts of the [Preset](#preset) are defined.

## Connection

Connects two [Nodes](#node) in the same area. Contains a set of [Requirements](#requirement) that define whether the [Generator](#generator) and [Solver](#solver) are allowed to cross it.

## Dangerous Action

Any action which, upon being performed, cuts off access to nodes that were previously accessible.

## Dangerous Logic
[Logic](#logic) that allows Actions to be performed which may place the game in an unbeatable state. Different from a [Point of No Return](#point-of-no-return) in that this is a primarily player-oriented issue; the game can still be beatable, but performing Actions in the wrong order can cause a player to experience this issue even though the [Seed](#seed) is valid.

Examples:
- Collecting the Gravity Suit in Metroid Prime, which makes Underwater Slope Jumps impossible

## Database

The sum total of all data that represents a game within Randovania. Contains a list of [Worlds](#world), a [Resource Database](#resource-database), a [Victory Condition](#victory-condition), and any other information necessary to represent the game.

## Dock

Represents some link between two [Areas](#area) that are directly adjacent. Docks usually represent things like doors, bridges, or other direct connections between areas, unlike [Teleporters](#teleporter), which represent means of travelling between two distant or disjointed Areas. Usually used to link two Areas within the same [World](#world), although it is possible for Docks to connect Areas between different Worlds.

## Event

A [Resource](#resource) representing something a player may do to access more of the game. Events can only be completed once, and cannot be undone.

Examples:
- Activating a switch that unlocks a door elsewhere
- Defeating a boss which causes the states of other rooms to change

## Experimental

Any system or feature of Randovania which is not ready for public use.

## Game Patches

Has two meainings:

- Colloquially, any modification made to the game. Usually refers to specific changes made to the game, such as cutscene alterations, and not to the randomization process itself.

- In code, refers to the GamePatches class, which holds all per-layout game modifications for a single player. Crucially, this does not include cosmetic patches.

## Generator

The part of Randovania responsible for placing [Pickups](#pickup) in randomized games, as well as determing details like [Starting Items](#starting-items).

## Hint

A piece of text placed in the game world which may give the player information about their game. This is distinct from [Log Files](#log-file), which contain all details of a generated game, and are generally considered to be a form of cheating in most competitive settings.

## Item

A kind of [Resource](#resource) that represents something a player has during the game.

Examples:
- Space Jump Boots in Metroid Prime 1/2.
- Missiles in Metroid games.

## Item Check

Colloquial term for a [Pickup Node](#pickup-location-/-pickup-node), e.g. "Phazon Suit only opens up one check."

## Layout

Internal name for the output of the [Generator](#generator). Contains all modifications ([GamePatches](#game-patches)) for all players, along with a [Permalink](#permalink).

The GUI uses "randomized game", "generated game" or something similar instead.

Whenever [Plandomizers](#plandomizer) are supported, they'd be a hand-made layout.

## Log File

Colloquial term for a [LayoutDescription](#layout) serialized to a .rdvgame file. Also referred to as a Spoiler Log.

## Logic

A colloquial term for how a randomizer decides what actions to perform during generation. Can mean one of the following:
- Most often, the rules that govern what you need to reach certain in-game locations See [Database](#database) and [Requirement](#requirement).
- Predicting [Pickup](#pickup) placement based on patterns observed in the behavior of the [Generator](#generator).

## Multiworld

A multiplayer randomizer [Session](#session) in which the [Pickup Pool](#pickup-pool) for each player is shuffled together as a single pool, with [Pickups](#pickup) for any player being placed in a given player's [Layout](#layout). Each player will have a unique layout, and the required [Progression](#progression) will often jump back and forth between players.

## Node

Represents a point of interest within an [Area](#area), and may contain [Resources](#resource), such as [Docks](#dock) or [Pickups](#pickup). Nodes have [Connections](#connection) to all other Nodes in the same Area.

Nodes always refer to a specific point in space, sometimes with explicit coordinates.

## Nothing / Nothing Pickup

A [Pickup](#pickup) that, while physically present in the game world, grants the player nothing whatsoever upon being obtained. Players with obfuscated viewmodels will only be able to tell a Nothing apart from the other Pickups by collecting it.

## Patcher

The code responsible for making the actual game modifications, generally according to the results of [GamePatches](#game-patches).

## Permalink

String with all data necessary to generate a game/[LayoutDescription](#layout). Support for Permalinks are only guaranteed if using the same specific version, or when using stable releases, the same major.minor series.

For code: Contains one 32-bit int and one [Preset](#preset) for each player.

## Pickup

Represents something that can be collected. Gives a quantity of any number of [Items](#item). Can also be progressive, giving some Item based on which Items the player has.
When starting the [Generator](#generator), a [Pool of Pickups](#pickup-pool) is created based on the [Preset](#preset).

## Pickup Pool

The available pool of [Items](#item) that can be placed as [Pickups](#pickup) during generation, and rules governing how they should be placed. Also includes information about [Starting Items](#starting-items).

## Pickup Location / Pickup Node

Represents a [Node](#node) where a [Pickup](#pickup) can be found. All locations will be assigned a Pickup during generation.

## Plandomizer

A game where generation has been performed by hand, rather than by using the randomizer.

## Point of No Return

A Point of No Return (PONR) is a colloquial term for a [Dangerous Action](#dangerous-action). It is sometimes used to more specifically refer to Dangerous Actions involving travelling from one [Node](#node) to another, not including actions such as collecting [Events](#event) or [Pickups](#pickup) which are otherwise dangerous.

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

## Resource Database

The part of the [Database](#database) which defines all [Resources](#resource) relevant to the game. Can be visualized and modified in the [Data Editor](#data-editor).

## RNG

Acronym for "Random Number Generator". Commonly used in speedrunning communities as an alias to random/randomness.
This term is not used at all in the GUI and in the code only to describe an object of type `random.Random`.

## Seed

Commonly used to refer to a [Layout](#layout).

Internally, this is used only to refer to the value used to initialize a [Random Number Generator](#rng).

## Session

An instance of [Multiworld](#multiworld) play.

## Solver

The part of Randovania that takes a [Layout](#layout) and determines a path that can reach the [Victory Condition](#victory-condition).

By default, this process is run for all single-player Layouts after generation.

## Starting Items

[Items](#item) which a player is granted immediately upon starting the game.

## Teleporter

Any system that connects two conceptually disjointed [Areas](#area) of the game. Unlike [Docks](#dock), the areas they connect are not directly adjacent to one another. Teleporters are used to represent things like elevators, portals, fast-travel points, and, of course, actual teleporters. Teleporters are sually used to connect two distinct [Worlds](#world), though a Teleporter can also connect two Areas in the same World.

## Trick

A [Resource](#resource) that represents some non-trivial gameplay feat, usually achieved by exploiting some mechanic or glitch.

Examples:
- Slope Jumps in the Metroid Primes.

## Trivial

A [Requirement](#requirement) which is always considered possible to meet, regardless of the player's current [Resources](#resource).

## Vanilla

An unmodified copy of the game.

## Victory Condition

A single [Requirement](#requirement) defined for each game in order to determine whether the game's objective can be completed.

Examples:
- Reaching the Credits room in the Metroid Primes
- Achieving any of the three endings in Cave Story

## World

The largest subdivision used when mapping a game in Randovania. Worlds contain many [Areas](#area), and there are usually only a few Worlds per game.

Examples:
- Chozo Ruins in Metroid Prime
- Maridia in Super Metroid
