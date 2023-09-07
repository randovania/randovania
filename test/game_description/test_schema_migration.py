from __future__ import annotations

from randovania.game_description import data_reader, data_writer, game_migration


def test_round_trip_small(test_files_dir):
    # Setup
    original_data = test_files_dir.read_json("prime2_small_v1.json")
    migrated_data = game_migration.migrate_to_current(original_data)

    game = data_reader.decode_data(migrated_data)

    encoded_data = data_writer.write_game_description(game)
    encoded_data["used_trick_levels"] = None
    assert encoded_data == migrated_data
