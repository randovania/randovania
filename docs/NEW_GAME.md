
## Required Changes


In order to add support for a new game to Randovania, you will need to create a new folder, `randovania/games/{game-id}`, and add a `game_data.py` file to it containing a single variable, `game_data`, assigned to a GameData. This GameData must populate all fields except for the optional `patcher` field.

For specific details on each field, refer to the class definition in `randovania/games/game.py` for type annotations and further documentation. You can also refer to existing games' implementations.

Once the GameData has been created, the following steps are required:


1. In `randovania/games/game.py`, add your `{game-id}` as a new value to `RandovaniaGame`. Multiple words must be split with underscores. Also add an import to your module in `RandovaniaGame`'s `data` property.


2. Add an empty file named `__init__.py` to your game folder.


3. Add the new database file to `json_data/{game-id}.json` or `json_data/header.json` in your game folder.
The latter must have the world list split into multiple files. 
**TODO**: list minimum requirements for the database file (areas, docks?, etc.) 


4. Open Randovania > Edit > Database > Internal > {new game} and then press "Save as database". This ensures the 
database is saved as the split format, as well as the human-readable version.


5. Create a new default Preset for your new game:
   1. Create `presets/starter_preset.rdvpreset` in your game folder. You can copy over an existing preset.
   2. Add a valid unique uuid. Run `python -c "import uuid; print(uuid.uuid4())"` to generate one.
   3. Remove fields that are not present in `BaseConfiguration`.
   4. Remove all references to items and tricks of other games.
   5. Ensure your GameData includes an entry for this default preset.


6. Create the folder `item_database` in your game folder with the following content:
   1. `item-database.json`, with content `{"item_categories": {}, "items": {}, "ammo": {}, "default_items": {}}`.
   2. `default_state/ammo.json`, with content `{"maximum_ammo": {}, "items_state": {}}`.
   3. `default_state/major-items.json`, with content  `{"items_state": {}}`.


7. Run the unit tests. If some tests don't pass, one of the steps above have incorrect data.


### Correctly generating games

For a game to be correctly generated, it's necessary to be able to reach the victory condition. This will normally be
some requirement for a final boss event.
During development, this can be anything you want, which can help when the database is not complete.

While the database deals with items, the generator and layouts uses pickups. It's now necessary to configuring the new
game to have proper pickups:

1. Fill your game's `item_database`. Use another game's file for reference.


2. Update `major_items_configuration` and `ammo_configuration` in your game's starter preset.


3. Fill the default state in your game's `item_database`. (Needed for tests, but point of cleanup).


### Exporting games

In order to export a game, a patcher is required. Typically, the patcher will be included in Randovania for seamless exports. This is a requirement for non-experimental games. Experimental games, however, may prefer an alternative implementation: refer to Corruption as an example of exporting data to be passed to a standalone patcher.

**TODO**: details


### Multiworld

**TODO**
