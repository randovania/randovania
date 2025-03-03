import json

from randovania.game.game_enum import RandovaniaGame
from randovania.game_description.pickup.pickup_database import read_database


def test_migrate_pickup_database(test_files_dir):
    old_data_path = test_files_dir.joinpath("pickup_database", "prime2-old.json")
    with old_data_path.open() as f:
        old_data = json.load(f)

    # nothing to assert; just want to make sure the migration happens without error
    read_database(old_data, RandovaniaGame.METROID_PRIME_ECHOES)
