from __future__ import annotations

import base64
import datetime
import json
from typing import TYPE_CHECKING

import pytest
from fastapi.encoders import jsonable_encoder
from playhouse.shortcuts import dict_to_model, model_to_dict

from randovania.bitpacking import construct_pack
from randovania.network_common.remote_inventory import RemoteInventory
from randovania.network_common.session_visibility import MultiplayerSessionVisibility
from randovania.server import database

if TYPE_CHECKING:
    from collections.abc import Callable

    from test.server.conftest import RdvTestClient


def _handle_db_nonsense(test_client: RdvTestClient, session_setup: Callable[[], database.MultiplayerSession]) -> None:
    # The test client doesn't seem to play well with the database fixtures.
    # The solution I've found is to do everything inside the test client's event loop, like this

    @test_client.sa.app.post("/setup-db")
    def setup_db() -> dict:
        session = model_to_dict(session_setup(), backrefs=True)
        return jsonable_encoder(session, custom_encoder={bytes: lambda v: base64.b64encode(v).decode("utf-8")})


def test_admin_sessions(test_client, solo_two_world_session_setup) -> None:
    _handle_db_nonsense(test_client, solo_two_world_session_setup)

    # Run
    test_client.post("/setup-db")
    result = test_client.get("/sessions")

    # Assert
    whitespace = "\n                        "
    entry = ["<td>The Name</td>", "<td>10:20 UTC, 02 May 2020</td>", "<td>1</td>", "<td>2</td>", "<td>False</td>"]
    assert whitespace.join(entry) in result.text


def test_admin_sessions_paginated(test_client) -> None:
    # Setup
    def setup() -> database.MultiplayerSession:
        user = database.User.create(id=1234, name="The Name")
        for i in range(50):
            session = database.MultiplayerSession.create(
                name=f"Debug{i}",
                state=MultiplayerSessionVisibility.VISIBLE,
                creator=user,
                creation_date=datetime.datetime(2020, 5, 2, 10, 20, tzinfo=datetime.UTC),
            )
        return session

    _handle_db_nonsense(test_client, setup)

    # Run
    test_client.post("/setup-db")
    result = test_client.get("/sessions?page=2")

    # Assert
    prev_link = '<a href="http://testserver/sessions?page=1">Previous</a>'
    next_link = '<a href="http://testserver/sessions?page=3">Next</a>'
    assert prev_link in result.text
    assert next_link in result.text

    assert "Page 2 of 3." in result.text


def test_admin_session_missing(test_client, solo_two_world_session_setup) -> None:
    # Setup
    _handle_db_nonsense(test_client, solo_two_world_session_setup)

    # Run
    test_client.post("/setup-db")
    result = test_client.get("/session/2403")

    # Assert
    assert result.status_code == 404
    assert "Session not found" in result.text


def test_admin_session_exists(test_client, solo_two_world_session_setup) -> None:
    # Setup
    def setup() -> database.MultiplayerSession:
        session = solo_two_world_session_setup()
        assoc = database.WorldUserAssociation.get_by_instances(world=1, user=1234)
        assoc.inventory = construct_pack.encode(
            {"Charge": 1},
            RemoteInventory,
        )
        assoc.save()
        return session

    _handle_db_nonsense(test_client, setup)

    # Run
    test_client.post("/setup-db")
    result = test_client.get("/session/1")

    # Assert
    whitespace = "\n                        "
    entry1 = [
        "<td>The Name</td>",
        "<td>World 1</td>",
        "<td>prime1</td>",
        "<td>Disconnected</td>",
        "<td>Charge Beam x1</td>",
    ]
    entry2 = ["<td>The Name</td>", "<td>World 2</td>", "<td>prime2</td>", "<td>Disconnected</td>", "<td>Missing</td>"]
    assert whitespace.join(entry1) in result.text
    assert whitespace.join(entry2) in result.text


def test_delete_session_get(test_client, solo_two_world_session_setup) -> None:
    # Setup
    _handle_db_nonsense(test_client, solo_two_world_session_setup)

    # Run
    session_dict = json.loads(test_client.post("/setup-db").text)
    session_dict["layout_description_json"] = base64.b64decode(session_dict["layout_description_json"])
    result = test_client.get("/session/1/delete")

    # Assert
    assert '<button type="submit" formmethod="post">Confirm delete</button>' in result.text
    assert '<button type="submit" formaction="http://testserver/session/1">Cancel</button>' in result.text
    assert database.MultiplayerSession.get_by_id(1) == dict_to_model(database.MultiplayerSession, session_dict)


def test_toggle_admin_status_doesnt_exist(test_client, solo_two_world_session_setup) -> None:
    # Setup
    _handle_db_nonsense(test_client, solo_two_world_session_setup)

    # Run
    test_client.post("/setup-db")
    result = test_client.post("/session/9999/user/0/toggle_admin")

    assert result.status_code == 404
    assert "Membership not found" in result.text


@pytest.mark.parametrize("initial_admin", [False, True])
def test_toggle_admin_status(test_client, solo_two_world_session_setup, initial_admin) -> None:
    # Setup
    def setup() -> database.MultiplayerSession:
        session = solo_two_world_session_setup()

        member = database.MultiplayerMembership.get_by_ids(1234, 1)
        member.admin = initial_admin
        member.save()

        return session

    _handle_db_nonsense(test_client, setup)

    # Run
    test_client.post("/setup-db")
    result = test_client.post("/session/1/user/1234/toggle_admin")

    # Assert
    @test_client.sa.app.get("/check-toggled")
    def check_toggled():
        membership = database.MultiplayerMembership.get_by_ids(1234, 1)
        assert membership.admin is not initial_admin

    @test_client.sa.app.get("/check-new-audit")
    def check_new_audit():
        session = database.MultiplayerSession.get_by_id(1)
        audit_log = session.get_audit_log()
        last_entry = audit_log.entries[-1]
        assert f"Randovania Team made The Name{' not' if initial_admin else ''} an Admin" == last_entry.message

    assert (
        "Admin status of <code>The Name</code> toggled. <a href='http://testserver/session/1'>Return to session</a>"
        in result.text
    )
    test_client.get("/check-toggled")
    test_client.get("/check-new-audit")


def test_delete_session_post(test_client, solo_two_world_session_setup) -> None:
    # Setup
    _handle_db_nonsense(test_client, solo_two_world_session_setup)

    @test_client.sa.app.get("/check-deleted")
    def check_deleted():
        database.MultiplayerSession.get_by_id(1)

    # Run
    test_client.post("/setup-db")
    result = test_client.post("/session/1/delete")

    # Assert
    assert "Session deleted. <a href='http://testserver/sessions'>Return to list</a>" in result.text

    with pytest.raises(database.MultiplayerSession.DoesNotExist):
        test_client.get("/check-deleted")
