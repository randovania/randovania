from __future__ import annotations

import json

import pytest

from randovania.bitpacking import construct_pack
from randovania.network_common.remote_inventory import RemoteInventory
from randovania.server import database


def test_admin_sessions(test_client, solo_two_world_session) -> None:
    # Run
    result = test_client.get("/sessions")

    # Assert
    entry = "<td>The Name</td><td>2020-05-02 10:20:00+00:00</td><td>1</td><td>2</td><td>False</td></tr>"
    assert entry in result.text


def test_admin_session_missing(test_client) -> None:
    # Setup
    database.User.create(id=1234, name="The Name")

    # Run
    result = test_client.get("/session/1")

    # Assert
    assert result.status_code == 404
    assert json.loads(result.text) == {"detail": "Session not found"}


def test_admin_session_exists(test_client, solo_two_world_session) -> None:
    # Setup
    assoc = database.WorldUserAssociation.get_by_instances(world=1, user=1234)
    assoc.inventory = construct_pack.encode(
        {"Charge": 1},
        RemoteInventory,
    )
    assoc.save()

    # Run
    result = test_client.get("/session/1")

    entry1 = "<td>The Name</td><td>World 1</td><td>prime1</td><td>Disconnected</td><td>Charge Beam x1</td>"
    entry2 = "<td>The Name</td><td>World 2</td><td>prime2</td><td>Disconnected</td><td>Missing</td><td>False</td>"
    assert entry1 in result.text
    assert entry2 in result.text


def test_delete_session_get(test_client, solo_two_world_session) -> None:
    # Run
    result = test_client.get("/session/1/delete")

    assert result.text == '<form method="POST"><input type="submit" value="Confirm delete"></form>'
    assert database.MultiplayerSession.get_by_id(1) == solo_two_world_session


def test_delete_session_post(test_client, solo_two_world_session) -> None:
    # Run
    result = test_client.post("/session/1/delete")

    assert result.text == "Session deleted. <a href='http://testserver/sessions'>Return to list</a>"

    with pytest.raises(database.MultiplayerSession.DoesNotExist):
        database.MultiplayerSession.get_by_id(1)
