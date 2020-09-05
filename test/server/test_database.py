from peewee import SqliteDatabase

from randovania.server import database


def test_init(tmpdir):
    test_db = SqliteDatabase(':memory:')
    with test_db.bind_ctx(database.all_classes):
        test_db.connect(reuse_if_open=True)
        test_db.create_tables(database.all_classes)
