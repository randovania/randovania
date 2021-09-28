
## Required Changes


In order to add support for a new game to Randovania, the following places needs changes.

1. In `randovania/games/game.py`, add a new value to `RandovaniaGame`. Multiple words must be split with underscores.


2. Add the new database file to `randovania/data/json_data/{enum-value}.json` or `randovania/data/json_data/{enum-value}/header.json`.
The later must have the world list split into multiple files. 


3. Open Randovania > Edit > Database > Internal > {new game} and then press "Save as database". This ensures the 
database is saved as the split format, as well as the human-readable version.


4. Create a new default Preset for your new game:
   1. Create `randovania/data/presets/{enum-value}/starter_preset.rdvpreset`. You can copy over an existing preset.
   2. Add a valid unique uuid. Run `python -c "import uuid; print(uuid.uuid4())"` to generate one.
   3. Remove fields that are not present in `BaseConfiguration`.
   4. Remove all references to items and tricks of other games.
   5. Update `randovania/data/presets/presets.json` with a new entry for `{enum-value}/starter_preset.rdvpreset`.


5. Create `randovania/layout/{enum-value}/{enum-value}_configuration.py` with a new class `{enum-value}Configuration` 
that inherits from `BaseConfiguration` and implement the `game_enum` method.


6. Create `randovania/layout/{enum-value}/{enum-value}_cosmetic_patches.py` with a new class `{enum-value}CosmeticPatches`
that inherits from `BaseCosmeticPatches` and implement the `game` method.


7. Update `randovania/layout/game_to_class.py` and add the mappings of the new enum to the new classes.


8. Create `randovania/data/item_database/{enum-value}` with the following content:
   1. `item-database.json`, with content `{"item_categories": {}, "items": {}, "ammo": {}, "default_items": {}}`.
   2. `default_state/ammo.json`, with content `{"maximum_ammo": {}, "items_state": {}}`.
   3. `default_state/major-items.json`, with content  `{"items_state": {}}`.


9. Update `randovania/gui/game_specific_gui.py`, adding new values to `TAB_PROVIDER_FOR_GAME` and `COSMETIC_DIALOG_FOR_GAME`.
   1. You can leave `COSMETIC_DIALOG_FOR_GAME` for later.

   
10. Update `randovania/gui/lib/preset_describer.py`, adding an empty set to `_EXPECTED_ITEMS` for the new game enum and
a new entry to the if/elseif in `describe`.


11. Update `randovania/generator/item_pool/pool_creator.py`, adding a new function to `_GAME_SPECIFIC` for the
new game enum.


12. Run the unit tests. If some test don't pass, one of the steps above have incorrect data.


### Correctly generating games

For a game to be correctly generated, it's necessary to be able to reach the victory condition. This will normally be
some requirement for a final boss event.
During development, this can be anything you want, which can help when the database is not complete.

While the database deals with items, the generator and layouts uses pickups. It's now necessary to configuring the new
game to have proper pickups:

1. Fill `randovania/data/item_database/{enum-value}/item-database.json`. Use another game's file for reference.


2. Update `major_items_configuration` and `ammo_configuration` in `randovania/data/presets/{enum-value}/starter_preset.rdvpreset`.


3. Fill `randovania/data/item_database/{enum-value}/default_state` (needed for tests, but point of cleanup).


### Exporting games

Update `randovania/games/patcher_provider.py`, providing a instance of your new class that inherits from `Patcher`.

TODO: details


### Multiworld

TODO
