from __future__ import annotations

import datetime

import pytest

from randovania.bitpacking import construct_pack
from randovania.network_common.remote_inventory import RemoteInventory
from randovania.network_common.session_visibility import MultiplayerSessionVisibility
from randovania.server import database


def test_admin_sessions(test_client, solo_two_world_session) -> None:
    test_client.set_logged_in_user(1234)

    # Run
    result = test_client.get("/sessions")

    # Assert
    whitespace = "\n                        "
    entry = ["<td>The Name</td>", "<td>10:20 UTC, 02 May 2020</td>", "<td>1</td>", "<td>2</td>", "<td>False</td>"]
    assert whitespace.join(entry) in result.text


def test_admin_sessions_paginated(test_client) -> None:
    # Setup
    user = database.User.create(id=1234, name="The Name", admin=True)
    for i in range(50):
        database.MultiplayerSession.create(
            name=f"Debug{i}",
            state=MultiplayerSessionVisibility.VISIBLE,
            creator=user,
            creation_date=datetime.datetime(2020, 5, 2, 10, 20, tzinfo=datetime.UTC),
        )
    test_client.set_logged_in_user(1234)

    # Run
    result = test_client.get("/sessions?page=2")

    # Assert
    prev_link = '<a href="http://testserver/sessions?page=1">Previous</a>'
    next_link = '<a href="http://testserver/sessions?page=3">Next</a>'
    assert prev_link in result.text
    assert next_link in result.text

    assert "Page 2 of 3." in result.text


def test_admin_session_missing(test_client, solo_two_world_session) -> None:
    # Setup
    test_client.set_logged_in_user(1234)

    # Run
    result = test_client.get("/session/2403")

    # Assert
    assert result.status_code == 404
    assert "Session not found" in result.text


def test_admin_session_exists(test_client, solo_two_world_session) -> None:
    # Setup
    test_client.set_logged_in_user(1234)
    assoc = database.WorldUserAssociation.get_by_instances(world=1, user=1234)
    assoc.inventory = construct_pack.encode(
        {"Charge": 1},
        RemoteInventory,
    )
    assoc.save()

    # Run
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


def test_delete_session_get(test_client, solo_two_world_session) -> None:
    # Setup
    test_client.set_logged_in_user(1234)

    # Run
    session = database.MultiplayerSession.get_by_id(1)
    result = test_client.get("/session/1/delete")

    # Assert
    assert '<button type="submit" formmethod="post">Confirm delete</button>' in result.text
    assert '<button type="submit" formaction="http://testserver/session/1">Cancel</button>' in result.text
    assert database.MultiplayerSession.get_by_id(1) == session


def test_toggle_admin_status_doesnt_exist(test_client, solo_two_world_session) -> None:
    # Setup
    test_client.set_logged_in_user(1234)

    # Run
    result = test_client.post("/session/9999/user/0/toggle_admin")

    assert result.status_code == 404
    assert "Membership not found" in result.text


@pytest.mark.parametrize("initial_admin", [False, True])
def test_toggle_admin_status(test_client, solo_two_world_session, initial_admin) -> None:
    # Setup
    test_client.set_logged_in_user(1234)
    membership = database.MultiplayerMembership.get_by_ids(1234, 1)
    membership.admin = initial_admin
    membership.save()

    # Run
    result = test_client.post("/session/1/user/1234/toggle_admin")

    # Assert
    assert (
        "Admin status of <code>The Name</code> toggled. <a href='http://testserver/session/1'>Return to session</a>"
        in result.text
    )

    # Fetch from db again
    membership = database.MultiplayerMembership.get_by_ids(1234, 1)
    assert membership.admin is not initial_admin

    audit_log = solo_two_world_session.get_audit_log()
    last_entry = audit_log.entries[-1]
    assert f"Randovania Team made The Name{' not' if initial_admin else ''} an Admin" == last_entry.message


def test_delete_session_post(test_client, solo_two_world_session) -> None:
    # Setup
    test_client.set_logged_in_user(1234)

    # Run
    result = test_client.post("/session/1/delete")
    result.raise_for_status()

    # Assert
    assert "Session deleted. <a href='http://testserver/sessions'>Return to list</a>" in result.text

    with pytest.raises(database.MultiplayerSession.DoesNotExist):
        database.MultiplayerSession.get_by_id(1)


def test_delete_session_post_not_authorized(test_client) -> None:
    # Run
    result = test_client.post("/session/1/delete", headers={"Accept": "application/json"})
    assert result.status_code == 401
    assert result.json() == {"status_message": "401 Unauthorized", "detail": "Unknown user"}
