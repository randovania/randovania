from __future__ import annotations

from unittest.mock import MagicMock

import cryptography.fernet
import flask
import pytest
from peewee import SqliteDatabase

from randovania.games.game import RandovaniaGame
from randovania.server import database


@pytest.fixture()
def empty_database():
    old_db = database.db
    try:
        test_db = SqliteDatabase(":memory:")
        database.db = test_db
        with test_db.bind_ctx(database.all_classes):
            test_db.connect(reuse_if_open=True)
            yield test_db
    finally:
        database.db = old_db


@pytest.fixture()
def clean_database(empty_database):
    empty_database.create_tables(database.all_classes)
    return empty_database


@pytest.fixture()
def flask_app():
    app = flask.Flask("test_app")
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "secret"
    with app.app_context():
        yield app


@pytest.fixture()
def fernet():
    return cryptography.fernet.Fernet(b"s2D-pjBIXqEqkbeRvkapeDn82MgZXLLQGZLTgqqZ--A=")


@pytest.fixture()
def default_game_list(is_dev_version):
    return [g.value for g in RandovaniaGame.sorted_all_games() if g.data.defaults_available_in_game_sessions]


@pytest.fixture(name="server_app")
def server_app_fixture(flask_app):
    pytest.importorskip("engineio.async_drivers.threading")
    from randovania.server.server_app import ServerApp

    flask_app.config["SECRET_KEY"] = "key"
    flask_app.config["DISCORD_CLIENT_ID"] = 1234
    flask_app.config["DISCORD_CLIENT_SECRET"] = 5678
    flask_app.config["DISCORD_REDIRECT_URI"] = "http://127.0.0.1:5000/callback/"
    flask_app.config["FERNET_KEY"] = b"s2D-pjBIXqEqkbeRvkapeDn82MgZXLLQGZLTgqqZ--A="
    flask_app.config["GUEST_KEY"] = b"s2D-pjBIXqEqkbeRvkapeDn82MgZXLLQGZLTgqqZ--A="
    flask_app.config["ENFORCE_ROLE"] = None
    server = ServerApp(flask_app)
    server.metrics.summary = MagicMock()
    server.metrics.summary.return_value.side_effect = lambda x: x
    return server
