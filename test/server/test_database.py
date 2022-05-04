from unittest.mock import PropertyMock

import pytest
from peewee import SqliteDatabase

from randovania.layout.layout_description import LayoutDescription
from randovania.lib import construct_lib
from randovania.network_common.binary_formats import BinaryGameSessionEntry
from randovania.server import database


def test_init(tmpdir):
    test_db = SqliteDatabase(':memory:')
    with test_db.bind_ctx(database.all_classes):
        test_db.connect(reuse_if_open=True)
        test_db.create_tables(database.all_classes)


@pytest.mark.parametrize("has_description", [False, True])
def test_GameSession_create_session_entry(clean_database, has_description, test_files_dir, mocker):
    # Setup
    description = LayoutDescription.from_file(test_files_dir.joinpath("log_files", "seed_a.rdvgame"))
    someone = database.User.create(name="Someone")
    s = database.GameSession.create(name="Debug", num_teams=1, creator=someone)
    game_details = None
    if has_description:
        s.layout_description = description
        s.save()
        game_details = {
            'seed_hash': '5IENQWDS',
            'spoiler': True,
            'word_hash': 'Biostorage Cavern Watch',
        }

    # Run
    session = database.GameSession.get_by_id(1)
    result = session.create_session_entry()
    readable_result = construct_lib.convert_to_raw_python(BinaryGameSessionEntry.parse(result))

    # Assert
    assert readable_result == {
        'allowed_games': ['prime1', 'prime2'],
        'game_details': game_details,
        'generation_in_progress': None,
        'id': 1,
        'name': 'Debug',
        'players': [],
        'presets': [],
        'state': 'setup',
    }
