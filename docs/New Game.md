
## Required Changes

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

### Correctly generating games

For a game to be correctly generated, it's necessary to be able to reach the victory condition. This will normally be
some requirement for a final boss event.
During development, this can be anything you want, which can help when the database is not complete.

While the database deals with items, the generator and layouts uses pickups. It's now necessary to configuring the new
game to have proper pickups:

1. Fill your game's `pickup_database/pickup-database.json`. Use another game's file for reference.


2. Update `standard_pickup_configuration` and `ammo_pickup_configuration` in your game's starter preset.



### Exporting games

In order to export a game, a patcher is required. Typically, the patcher will be included in Randovania for seamless exports. This is a requirement for non-experimental games. Experimental games, however, may prefer an alternative implementation: refer to Corruption as an example of exporting data to be passed to a standalone patcher.

**TODO**: details


### Multiworld

**TODO**
