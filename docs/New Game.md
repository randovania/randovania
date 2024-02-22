
# Required Changes

Randovania provides a command line tool for making the necessary changes to start adding a new game:

```commandline
python -m randovania development add-new-game --enum-name FANCY_EXPLORATION --enum-value fancy_exploration --short-name Fancy --long-name "Fancy Exploration: The Adventure"
```
Replace the values of the command with appropriate values for your game. The meaning is:
- enum-name: Used in Randovania's codebase to refer to your game, via `RandovaniaGame.FANCY_EXPLORATION`.
- enum-value: Used for file and file paths to refer to your game. Very hard to be changed in the future.
- short-name: Used to prefix all classes used by your game, and in user-facing elements that needs to be brief.
- long-name: Used in user-facing elements to mention your game.

The command check if the provided values fit the naming rules for each of these. 

Make sure you have followed the Developer setup and activated the virtual environment before running the command.

## Development Process

This is a rough outline on how the development process is for new games.
1. Make a thread in #randovania-dev in the [Randovania Discord server](https://discord.gg/M23gCxj6fw) to discuss your work. Please communicate with the core dev team there as much as possible. A Discord account is required, as said server is necessary to test the development builds, as well as receiving feedback and bugs for your game.

2. Open a Pull Request whenever you think you've got the bare minimum. "Bare minimum" means that you're confident that you will be able to take your game from that initial PR to stable in a reasonable amount of time. For some, this will be relatively early, for others rather late. But the time ultimately doesn't matter much, as long as the dev team is kept informed of your progress.

3. Ask the core dev team for a review, address their reviews, and repeat until the PR is merged.

4. Send Pull Requests for individual features/changes of your game implementation.

It is important to reiterate that communication with us is key. If you open a Pull Request to a new game out of the blue, without having it ever discussed with us, we may close your PR and ask you to talk with us first. Similarly, if you keep things private or are generally uncommunicative with us, then we'll also be less inclined to work with you.

## Correctly generating games

For a game to be correctly generated, it's necessary to be able to reach the victory condition. This will normally be
some requirement for a final boss event.
During development, this can be anything you want, which can help when the database is not complete.

While the database deals with items, the generator and layouts uses pickups. It's now necessary to configuring the new
game to have proper pickups:

1. Fill your game's `pickup_database/pickup-database.json`. Use another game's file for reference.


2. Update `standard_pickup_configuration` and `ammo_pickup_configuration` in your game's starter preset.


## Exporting games

Up to now, everything is just theoretical values inside Randovania. The next step is applying these modifications to the game. 

In most cases, this involves reading the files from a user-provided copy of the game and creating either a new ROM/ISO
file or a mod file.

This process is split into two parts:

### Patch Data Factory

Each game defines a class that inherits from `PatchDataFactory`. Given a `LayoutDescription`, a `CosmeticPatches` and 
`PlayersConfiguration`, it creates a JSON Object that will be passed as an argument to the Game Exporter.

### Game Exporter

Each game also defines a class that inherits from `GameExporter`. Given the JSON created by the `PatchDataFactory` and a
`GameExportParams`, provided by your game's `GameExportDialog`, it's expected to create all the necessary files for the
user to play the game.

Since Randovania does not modify the game files, a separate Python package must be created which is responsible for
these changes. This package is called the patcher for the game.

You are free to implement this package however you want, but we recommend the following:

#### Input Data

The arguments for the patcher should be:
- A json file, also called the patcher data
- Paths to necessary game files (input path)
- Paths to an output folder (output path)
- A status update function

Any other parameter should come from the json file.

#### Language

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

#### Standalone Use

Allow your patcher to be used directly in the command line, by passing the game files and a json file.

This makes it easy to test the patcher without having to run it through Randovania, and helps better identify issues.

#### Json Schema

Define a [JSON Schema](https://json-schema.org/understanding-json-schema/) that defines the structure of the patcher data.
This makes for a good documentation of what is the input for the patcher, as well as a very good safety against
misconfiguration in Randovania.

### Multiworld

Before a game can work in Multiworld, it must first work properly as a solo game. It is highly recommended to finish the basic integration first.

**TODO**

# Rules for new games

Randovania maintains a high quality standard for game integration. In order for a new game to be accepted,
the following rules must be adhered to:

- An owner for the game. The owner is expected to be available and willing to maintain their game for the foreseeable future.
- A reviewer of Logic changes, separate from the owner.
- An open source patcher, with a license that allows us to fork your patcher and continue it in case of abandonment. Licenses such as GPLv3 or Apache 2 are great options.
- Proper test coverage of new code, at least the part included in Randovania.
