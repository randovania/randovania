import cryptography.fernet
import flask
import pytest
from peewee import SqliteDatabase

from randovania.server import database


@pytest.fixture()
def clean_database():
    old_db = database.db
    try:
        test_db = SqliteDatabase(':memory:')
        database.db = test_db
        with test_db.bind_ctx(database.all_classes):
            test_db.connect(reuse_if_open=True)
            test_db.create_tables(database.all_classes)
            yield test_db
    finally:
        database.db = old_db


@pytest.fixture()
def flask_app():
    app = flask.Flask("test_app")
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "secret"
    with app.app_context():
        yield app


@pytest.fixture()
def fernet():
    return cryptography.fernet.Fernet(b's2D-pjBIXqEqkbeRvkapeDn82MgZXLLQGZLTgqqZ--A=')
