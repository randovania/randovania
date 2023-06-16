import datetime
import datetime
import uuid
from unittest.mock import MagicMock, call

from randovania.bitpacking import construct_dataclass
from randovania.network_common import multiplayer_session
from randovania.network_common.multiplayer_session import MultiplayerSessionAuditLog, \
    MultiplayerSessionAuditEntry
from randovania.network_common.session_state import MultiplayerSessionState
from randovania.server import database
from randovania.server.multiplayer import session_common


def test_emit_session_meta_update(session_update, flask_app, mocker, default_game_list):
    mock_emit: MagicMock = mocker.patch("flask_socketio.emit")

    session_json = {
        "id": 1,
        "name": "Debug",
        "state": MultiplayerSessionState.IN_PROGRESS.value,
        "users_list": [
            {
                "id": 1234,
                "name": "The Name",
                "admin": True,
                'worlds': {},
            },
            {
                "id": 1235,
                "name": "Other",
                "admin": False,
                'worlds': {},
            },
        ],
        "worlds": [
            {'id': '67d75d0e-da8d-4a90-b29e-cae83bcf9519',
             'name': 'World1',
             'preset_raw': '{}'},
            {'id': 'd0f7ed70-66b0-413c-bc13-f9f7fb018726',
             'name': 'World2',
             'preset_raw': '{}'},
        ],
        "game_details": {
            "spoiler": True,
            "word_hash": "Words of O-Lir",
            "seed_hash": "ABCDEFG",
        },
        "generation_in_progress": None,
        'allowed_games': default_game_list,
    }

    # Run
    with flask_app.test_request_context():
        session_common.emit_session_meta_update(session_update)

    # Assert
    mock_emit.assert_called_once_with(
        "multiplayer_session_meta_update",
        session_json,
        room=f"game-session-{session_update.id}",
        namespace='/',
    )


def test_emit_session_actions_update(session_update, flask_app, mocker):
    mock_emit: MagicMock = mocker.patch("flask_socketio.emit")

    actions = multiplayer_session.MultiplayerWorldActions(
        session_id=1,
        actions=[multiplayer_session.MultiplayerWorldAction(
            provider=uuid.UUID('67d75d0e-da8d-4a90-b29e-cae83bcf9519'),
            receiver=uuid.UUID('d0f7ed70-66b0-413c-bc13-f9f7fb018726'),
            pickup="The Pickup",
            location=0,
            time=datetime.datetime(2020, 5, 2, 10, 20, tzinfo=datetime.timezone.utc),
        )]
    )

    # Run
    with flask_app.test_request_context():
        session_common.emit_session_actions_update(session_update)

    # Assert
    mock_emit.assert_called_once_with(
        "multiplayer_session_actions_update",
        construct_dataclass.encode_json_dataclass(actions),
        room=f"game-session-{session_update.id}",
        namespace='/',
    )


def test_emit_session_audit_update(session_update, flask_app, mocker):
    mock_emit: MagicMock = mocker.patch("flask_socketio.emit")

    database.MultiplayerAuditEntry.create(session=session_update, user=1234, message="Did something",
                                          time=datetime.datetime(2020, 5, 2, 10, 20, tzinfo=datetime.timezone.utc))
    database.MultiplayerAuditEntry.create(session=session_update, user=1235, message="Did something else",
                                          time=datetime.datetime(2020, 5, 3, 10, 20, tzinfo=datetime.timezone.utc))

    audit_log = MultiplayerSessionAuditLog(
        session_id=session_update.id,
        entries=[
            MultiplayerSessionAuditEntry(user="The Name", message="Did something",
                                         time=datetime.datetime(2020, 5, 2, 10, 20, tzinfo=datetime.timezone.utc)),
            MultiplayerSessionAuditEntry(user="Other", message="Did something else",
                                         time=datetime.datetime(2020, 5, 3, 10, 20, tzinfo=datetime.timezone.utc)),
        ]
    )

    # Run
    with flask_app.test_request_context():
        session_common.emit_session_audit_update(session_update)

    # Assert
    mock_emit.assert_called_once_with(
        "multiplayer_session_audit_update",
        construct_dataclass.encode_json_dataclass(audit_log),
        room=f"game-session-{session_update.id}",
        namespace='/',
    )


def test_join_game_session(mocker):
    mock_join_room = mocker.patch("flask_socketio.join_room")
    membership = MagicMock()
    membership.session.id = "session_id"
    membership.user.id = "user_id"

    session = {}
    sio = MagicMock()
    sio.session.return_value.__enter__.return_value = session

    # Run
    session_common.join_multiplayer_session(sio, membership)

    # Assert
    mock_join_room.assert_has_calls([
        call("game-session-session_id"),
        call("game-session-session_id-user_id"),
    ])
    assert session == {
        "multiplayer_sessions": ["session_id"],
    }


def test_leave_game_session_with_session(mocker):
    # Setup
    mock_leave_room: MagicMock = mocker.patch("flask_socketio.leave_room")
    user = MagicMock()
    user.id = "user_id"
    sio = MagicMock()
    sio.get_current_user = lambda: user

    session = {"multiplayer_sessions": ["session_id"]}
    sio.session = MagicMock()
    sio.session.return_value.__enter__.return_value = session

    # Run
    session_common.leave_multiplayer_sessions(sio)

    # Assert
    mock_leave_room.assert_has_calls([
        call("game-session-session_id"),
        call("game-session-session_id-user_id"),
    ])
    assert session == {}


def test_leave_game_session_without_session(mocker):
    # Setup
    mock_leave_room: MagicMock = mocker.patch("flask_socketio.leave_room")
    sio = MagicMock()
    sio.session = MagicMock()
    sio.session.return_value.__enter__.return_value = {}

    # Run
    session_common.leave_multiplayer_sessions(sio)

    # Assert
    mock_leave_room.assert_not_called()
