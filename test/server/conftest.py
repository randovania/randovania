from __future__ import annotations

from typing import TYPE_CHECKING

import cryptography.fernet
import pytest
from fastapi.testclient import TestClient
from peewee import SqliteDatabase

from randovania.game.game_enum import RandovaniaGame
from randovania.network_common.configuration import NetworkConfiguration
from randovania.server import database
from randovania.server.configuration import ServerConfiguration

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture
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


@pytest.fixture
def clean_database(empty_database):
    empty_database.create_tables(database.all_classes)
    return empty_database


@pytest.fixture
def fernet():
    return cryptography.fernet.Fernet(b"s2D-pjBIXqEqkbeRvkapeDn82MgZXLLQGZLTgqqZ--A=")


@pytest.fixture
def default_game_list(is_dev_version):
    return [g.value for g in RandovaniaGame.sorted_all_games() if g.data.defaults_available_in_game_sessions]


@pytest.fixture(name="server_app")
def server_app_fixture():
    pytest.importorskip("engineio.async_drivers.threading")
    from randovania.server.server_app import ServerApp

    server_config = ServerConfiguration(
        secret_key="key", discord_client_secret="5678", fernet_key="s2D-pjBIXqEqkbeRvkapeDn82MgZXLLQGZLTgqqZ--A="
    )
    configuration = NetworkConfiguration(
        server_address="http://127.0.0.1:5000",
        socketio_path="/socket.io",
        guest_secret="s2D-pjBIXqEqkbeRvkapeDn82MgZXLLQGZLTgqqZ--A=",
        server_config=server_config,
    )

    server = ServerApp(configuration)
    # server.metrics.summary = MagicMock()
    # server.metrics.summary.return_value.side_effect = lambda x: x
    return server


@pytest.fixture(name="test_client")
def test_client_fixture(server_app) -> Generator[TestClient, None, None]:
    with TestClient(server_app.app) as client:
        yield client
