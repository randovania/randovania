from randovania.game_description import default_database, integrity_check


def test_find_database_errors(game_enum):
    # Setup
    game = default_database.game_description_for(game_enum)

    # Run
    errors = integrity_check.find_database_errors(game)

    # Assert
    assert errors == []
