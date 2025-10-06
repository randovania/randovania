from __future__ import annotations

import datetime
import uuid
from unittest.mock import MagicMock

import pytest

from randovania.bitpacking import construct_pack
from randovania.network_common import multiplayer_session
from randovania.network_common.audit import AuditEntry
from randovania.network_common.multiplayer_session import MultiplayerSessionAuditLog
from randovania.network_common.session_visibility import MultiplayerSessionVisibility
from randovania.server import database
from randovania.server.multiplayer import session_common


async def test_emit_session_meta_update(session_update, mock_sa, default_game_list):
    mock_emit = mock_sa.sio.emit

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
            {
                "id": "67d75d0e-da8d-4a90-b29e-cae83bcf9519",
                "name": "World1",
                "preset_raw": "{}",
                "has_been_beaten": False,
            },
            {
                "id": "d0f7ed70-66b0-413c-bc13-f9f7fb018726",
                "name": "World2",
                "preset_raw": "{}",
                "has_been_beaten": False,
            },
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
    await session_common.emit_session_meta_update(mock_sa, session_update)

    # Assert
    mock_emit.assert_awaited_once_with(
        "multiplayer_session_meta_update",
        session_json,
        room=f"multiplayer-session-{session_update.id}",
        namespace="/",
    )


async def test_emit_session_actions_update(session_update, mock_sa):
    mock_emit = mock_sa.sio.emit

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
    await session_common.emit_session_actions_update(mock_sa, session_update)

    # Assert
    mock_emit.assert_awaited_once_with(
        "multiplayer_session_actions_update",
        construct_pack.encode(actions),
        room=f"multiplayer-session-{session_update.id}",
        namespace="/",
    )


async def test_emit_session_audit_update(session_update, mock_sa):
    mock_emit = mock_sa.sio.emit

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
            AuditEntry(
                user="The Name",
                message="Did something",
                time=datetime.datetime(2020, 5, 2, 10, 20, tzinfo=datetime.UTC),
            ),
            AuditEntry(
                user="Other",
                message="Did something else",
                time=datetime.datetime(2020, 5, 3, 10, 20, tzinfo=datetime.UTC),
            ),
        ],
    )

    # Run
    await session_common.emit_session_audit_update(mock_sa, session_update)

    # Assert
    mock_emit.assert_awaited_once_with(
        "multiplayer_session_audit_update",
        construct_pack.encode(audit_log),
        room=f"multiplayer-session-{session_update.id}",
        namespace="/",
    )


async def test_join_room(mock_sa):
    mock_join_room = mock_sa.sio.enter_room
    multi_session = MagicMock()
    multi_session.id = 1234

    session = {}
    mock_sa.sio.session.return_value.__aenter__.return_value = session

    # Run
    await session_common.join_room(mock_sa, "TheSid", multi_session)

    # Assert
    mock_join_room.assert_awaited_once_with("TheSid", "multiplayer-session-1234")
    assert session == {
        "multiplayer_sessions": [1234],
    }


@pytest.mark.parametrize("had_session", [False, True])
async def test_leave_room(mock_sa, had_session):
    # Setup
    mock_leave_room = mock_sa.sio.leave_room

    multi_session = MagicMock()
    multi_session.id = 7890

    session = {"multiplayer_sessions": [7890] if had_session else []}
    mock_sa.sio.session.return_value.__aenter__.return_value = session

    # Run
    await session_common.leave_room(mock_sa, "TheSid", multi_session.id)

    # Assert
    mock_leave_room.assert_awaited_once_with("TheSid", "multiplayer-session-7890")
    assert session == {"multiplayer_sessions": []}


@pytest.mark.parametrize("had_session", [False, True])
async def test_leave_all_rooms(mock_sa, had_session):
    # Setup
    mock_leave_room = mock_sa.sio.leave_room

    if had_session:
        session = {"multiplayer_sessions": [5678]}
    else:
        session = {}

    mock_sa.sio.session.return_value.__aenter__.return_value = session

    # Run
    await session_common.leave_all_rooms(mock_sa, "TheSid")

    # Assert
    if had_session:
        mock_leave_room.assert_awaited_once_with("TheSid", "multiplayer-session-5678")
    else:
        mock_leave_room.assert_not_called()
    assert session == {}
