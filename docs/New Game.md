# Rules for new games

Randovania maintains a high quality standard for game integration. In order for a new game to be accepted,
the following rules must be adhered to:

- An owner for the game. The owner is expected to be available and willing to maintain their game for the foreseeable future.
- A reviewer of Logic changes, separate from the owner.
- An open source patcher, with a license that allows us to fork your patcher and continue it in case of abandonment. Licenses such as GPLv3 or Apache 2 are great options.
- Proper test coverage of new code, at least the part included in Randovania.

# Development Process

This is a rough outline on how the development process is for new games.
1. Make a thread in #randovania-dev in the [Randovania Discord server](https://discord.gg/M23gCxj6fw) to discuss your work. Please communicate with the core dev team there as much as possible.
A Discord account is required, as said server is necessary to test the development builds, as well as receiving feedback and bugs for your game.

2. Open a Pull Request whenever you think you've got the bare minimum. "Bare minimum" means that you're confident that you will be able to take your game from that initial PR to stable in a reasonable amount of time. For some, this will be relatively early, for others rather late. But the time ultimately doesn't matter much, as long as the dev team is kept informed of your progress.

3. Ask the core dev team for a review, address their reviews, and repeat until the PR is merged.

4. Send Pull Requests for individual features/changes of your game implementation.

It is important to reiterate that communication with us is key. If you open a Pull Request to a new game out of the blue, without having it ever discussed with us, we may close your PR and ask you to talk with us first.
Similarly, if you keep things private or are generally uncommunicative with us, then we'll also be less inclined to work with you.

# Adding a new game entry

Randovania provides a command line tool for making the necessary changes to start adding a new game.
First, make sure you have followed the Developer setup and activated the virtual environment as explained in the readme. Then you can run the following command:

```commandline
python -m randovania development add-new-game --enum-name FANCY_EXPLORATION --enum-value fancy_exploration --short-name Fancy --long-name "Fancy Exploration: The Adventure"
```
Replace the values of the command with appropriate values for your game. The meaning is:
- enum-name: Used in Randovania's codebase to refer to your game, via `RandovaniaGame.FANCY_EXPLORATION`.
- enum-value: Used for file and file paths to refer to your game. Very hard to be changed in the future.
- short-name: Used to prefix all classes used by your game, and in user-facing elements that needs to be brief.
- long-name: Used in user-facing elements to mention your game.

The command check if the provided values fit the naming rules for each of these. 

## Basic game structure

Here's a very basic overview of how to go from nothing to an exported game.
Feel free to reference how already existing games implement or deal with certain steps.

### Correctly generating games

#### Logic Database

Setup a logic database. It contains a logical representation on all places one can visit, how they connect to each other, and defines all collectable resources/tricks/events and more that exist in the game.
It also defines a victory condition. This will normally be some requirement for a final boss event, but during development, this can be anything you want, which can help when the database is not complete. 
When first creating the database, it is *highly* recommended to try to automate the process as much as you can. This usually means having a separate program/script that can read the games internal structures, then building RDV's regions, areas, nodes from the read structures, and populating the `extra` field with any existing internal data that exists for them. Not automating it means having a very long and painful process to set them all up manually.

Further documentation:
- [Glossary entry](https://github.com/randovania/randovania/blob/main/docs/Glossary.md#database)
- [Documentation of the DB format](https://github.com/randovania/randovania/blob/main/docs/Database%20Format.md)
- [Documentation on how to do DB editing](https://github.com/randovania/randovania/blob/main/docs/Database%20Editor.md)
- [Python file](https://github.com/randovania/randovania/blob/main/randovania/game_description/game_description.py)

#### Pickup Database

Setup a pickup database. It contains all the items and their attributes. You can do so by editing `pickup_database/pickup-database.json` in a text editor.
You also need to update `standard_pickup_configuration` and `ammo_pickup_configuration` in your game's starter preset to reflect your pickup DB.

Further Documentation:
- [Glossary entry for Pickup](https://github.com/randovania/randovania/blob/main/docs/Glossary.md#pickup)
- Python file for a [StandardPickupDefinition](https://github.com/randovania/randovania/blob/main/randovania/game_description/pickup/standard_pickup.py) and an [AmmoPickupDefinition](https://github.com/randovania/randovania/blob/main/randovania/game_description/pickup/ammo_pickup.py)

#### Configuration & Generation Parameters

Each game has a class inheriting from `GameConfiguration`, which defines options that can be changed by a player before generation. The options themselves can be basically anything; they don't need to necessarily affect generation/logic. However its recomended to have purely visual changes as cosmetic options instead.

A game is also able to define parameters which drastically change generation. This can for example be events that are already cleared or starting already with certain items. When setting up a new game, you can usually ignore these for most of the time in development, so they're not explained very in-depth here.

Further documentation:
- Glossary entry [Configuration](https://github.com/randovania/randovania/blob/main/docs/Glossary.md#configuration)
- Python file for the [BaseConfiguration](https://github.com/randovania/randovania/blob/main/randovania/layout/base/base_configuration.py) and [GameGenerator](https://github.com/randovania/randovania/blob/main/randovania/game/generator.py)


After all of the above is done, you are able to generate games.

### Exporting games

Up to now, everything is just theoretical values inside Randovania. The next step is applying these modifications to the game. 

In most cases, this involves reading the files from a user-provided copy of the game and creating either a new ROM/ISO
file or a mod file.

This process is split into two parts:

#### Patch Data Factory

Each game defines a class that inherits from `PatchDataFactory`. Given a `LayoutDescription`, a `CosmeticPatches` and
`PlayersConfiguration`, it creates a JSON Object that will be passed as an argument to the Game Exporter.
There are no restrictions or rules by Randovania on how the JSON object has to be laid out, that is entirely up to the developer on how they want/need it.

#### Game Exporter

Each game also defines a class that inherits from `GameExporter`. Given the JSON created by the `PatchDataFactory` and a
`GameExportParams`, provided by your game's `GameExportDialog`, it's expected to create all the necessary files for the
user to play the game.

Since Randovania does not modify the game files, a separate Python package must be created which is responsible for
these changes. This package is called the patcher for the game.

You are free to implement this package however you want, but we recommend the following:

##### Input Data

The arguments for the patcher should be:
- A json file, also called the patcher data (the JSON that the `PatchDataFactory` creates).
- Paths to necessary game files (input path)
- Paths to an output folder (output path)
- A status update function

Any other parameters should come from the json file.

##### Language

Best:
- Python

Good (Known to integrate without issues):
- C
- C++
- Rust
- Lua

Likely Good (Should integrate well, never tested):
- Languages that compile to static library, such as Go

Ok (Expect additional work to integrate properly, avoid if possible):
- C#

Avoid languages that require the user to install a runtime, such as Java.

##### Standalone Use

Allow your patcher to be used directly in the command line, by passing the game files and a json file.

This makes it easy to test the patcher without having to run it through Randovania, and helps better identify issues.

##### Json Schema

Define a [JSON Schema](https://json-schema.org/understanding-json-schema/) that defines the structure of the patcher data.
This makes for a good documentation of what is the input for the patcher, as well as a very good safety against
misconfiguration in Randovania.

# Multiworld

Before a game can work in Multiworld, it must first work properly as a solo game. It is highly recommended to finish the basic integration first.

**TODO**
