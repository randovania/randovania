from __future__ import annotations

import datetime
import uuid
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from randovania.bitpacking import construct_pack
from randovania.network_common import multiplayer_session
from randovania.network_common.multiplayer_session import MultiplayerSessionAuditEntry, MultiplayerSessionAuditLog
from randovania.network_common.session_visibility import MultiplayerSessionVisibility
from randovania.server import database
from randovania.server.multiplayer import session_common

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


def test_emit_session_meta_update(session_update, flask_app, mocker, default_game_list):
    mock_emit: MagicMock = mocker.patch("flask_socketio.emit")

    session_json = {
        "id": 1,
        "name": "Debug",
        "visibility": MultiplayerSessionVisibility.VISIBLE.value,
        "users_list": [
            {
                "id": 1234,
                "name": "The Name",
                "admin": True,
                "ready": False,
                "worlds": {},
            },
            {
                "id": 1235,
                "name": "Other",
                "admin": False,
                "ready": True,
                "worlds": {},
            },
        ],
        "worlds": [
            {"id": "67d75d0e-da8d-4a90-b29e-cae83bcf9519", "name": "World1", "preset_raw": "{}"},
            {"id": "d0f7ed70-66b0-413c-bc13-f9f7fb018726", "name": "World2", "preset_raw": "{}"},
        ],
        "game_details": {
            "spoiler": True,
            "word_hash": "Words of O-Lir",
            "seed_hash": "ABCDEFG",
        },
        "generation_in_progress": None,
        "allowed_games": default_game_list,
        "allow_coop": False,
        "allow_everyone_claim_world": False,
    }

    # Run
    with flask_app.test_request_context():
        session_common.emit_session_meta_update(session_update)

    # Assert
    mock_emit.assert_called_once_with(
        "multiplayer_session_meta_update",
        session_json,
        room=f"multiplayer-session-{session_update.id}",
        namespace="/",
    )


def test_emit_session_actions_update(session_update, flask_app, mocker):
    mock_emit: MagicMock = mocker.patch("flask_socketio.emit")

    actions = multiplayer_session.MultiplayerSessionActions(
        session_id=1,
        actions=[
            multiplayer_session.MultiplayerSessionAction(
                provider=uuid.UUID("67d75d0e-da8d-4a90-b29e-cae83bcf9519"),
                receiver=uuid.UUID("d0f7ed70-66b0-413c-bc13-f9f7fb018726"),
                pickup="The Pickup",
                location=0,
                time=datetime.datetime(2020, 5, 2, 10, 20, tzinfo=datetime.UTC),
            )
        ],
    )

    # Run
    with flask_app.test_request_context():
        session_common.emit_session_actions_update(session_update)

    # Assert
    mock_emit.assert_called_once_with(
        "multiplayer_session_actions_update",
        construct_pack.encode(actions),
        room=f"multiplayer-session-{session_update.id}",
        namespace="/",
    )


def test_emit_session_audit_update(session_update, flask_app, mocker):
    mock_emit: MagicMock = mocker.patch("flask_socketio.emit")

    database.MultiplayerAuditEntry.create(
        session=session_update,
        user=1234,
        message="Did something",
        time=datetime.datetime(2020, 5, 2, 10, 20, tzinfo=datetime.UTC),
    )
    database.MultiplayerAuditEntry.create(
        session=session_update,
        user=1235,
        message="Did something else",
        time=datetime.datetime(2020, 5, 3, 10, 20, tzinfo=datetime.UTC),
    )

    audit_log = MultiplayerSessionAuditLog(
        session_id=session_update.id,
        entries=[
            MultiplayerSessionAuditEntry(
                user="The Name",
                message="Did something",
                time=datetime.datetime(2020, 5, 2, 10, 20, tzinfo=datetime.UTC),
            ),
            MultiplayerSessionAuditEntry(
                user="Other",
                message="Did something else",
                time=datetime.datetime(2020, 5, 3, 10, 20, tzinfo=datetime.UTC),
            ),
        ],
    )

    # Run
    with flask_app.test_request_context():
        session_common.emit_session_audit_update(session_update)

    # Assert
    mock_emit.assert_called_once_with(
        "multiplayer_session_audit_update",
        construct_pack.encode(audit_log),
        room=f"multiplayer-session-{session_update.id}",
        namespace="/",
    )


def test_join_room(mocker: MockerFixture):
    mock_join_room = mocker.patch("flask_socketio.join_room")
    multi_session = MagicMock()
    multi_session.id = 1234

    session = {}
    sa = MagicMock()
    sa.session.return_value.__enter__.return_value = session

    # Run
    session_common.join_room(sa, multi_session)

    # Assert
    mock_join_room.assert_called_once_with("multiplayer-session-1234")
    assert session == {
        "multiplayer_sessions": [1234],
    }


@pytest.mark.parametrize("had_session", [False, True])
def test_leave_room(mocker: MockerFixture, had_session):
    # Setup
    mock_leave_room: MagicMock = mocker.patch("flask_socketio.leave_room")

    multi_session = MagicMock()
    multi_session.id = 7890

    sa = MagicMock()

    session = {"multiplayer_sessions": [7890] if had_session else []}
    sa.session = MagicMock()
    sa.session.return_value.__enter__.return_value = session

    # Run
    session_common.leave_room(sa, multi_session.id)

    # Assert
    mock_leave_room.assert_called_once_with("multiplayer-session-7890")
    assert session == {"multiplayer_sessions": []}


@pytest.mark.parametrize("had_session", [False, True])
def test_leave_all_rooms(mocker: MockerFixture, had_session):
    # Setup
    mock_leave_room: MagicMock = mocker.patch("flask_socketio.leave_room")

    if had_session:
        session = {"multiplayer_sessions": [5678]}
    else:
        session = {}
    sa = MagicMock()
    sa.session = MagicMock()
    sa.session.return_value.__enter__.return_value = session

    # Run
    session_common.leave_all_rooms(sa)

    # Assert
    if had_session:
        mock_leave_room.assert_called_once_with("multiplayer-session-5678")
    else:
        mock_leave_room.assert_not_called()
    assert session == {}
