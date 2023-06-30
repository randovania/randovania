import contextlib
import datetime
import uuid
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from randovania.network_common import error
from randovania.network_common.session_state import MultiplayerSessionState
from randovania.server import database
from randovania.server.multiplayer import session_api
from randovania.server.server_app import ServerApp


@pytest.mark.parametrize("limit", [None, 2, 3])
def test_list_sessions(clean_database, flask_app, limit):
    # Setup
    utc = datetime.timezone.utc
    someone = database.User.create(name="Someone")
    database.MultiplayerSession.create(name="Debug", num_teams=1, creator=someone,
                                       creation_date=datetime.datetime(2020, 10, 2, 10, 20, tzinfo=utc))
    database.MultiplayerSession.create(name="Other", num_teams=2, creator=someone,
                                       creation_date=datetime.datetime(2020, 1, 20, 5, 2, tzinfo=utc))
    database.MultiplayerSession.create(name="Third", num_teams=2, creator=someone,
                                       creation_date=datetime.datetime(2021, 1, 20, 5, 2, tzinfo=utc))
    state = MultiplayerSessionState.SETUP.value

    # Run
    result = session_api.list_sessions(MagicMock(), limit)

    # Assert
    expected = [
        {'has_password': False, 'id': 3, 'state': state, 'name': 'Third', 'num_players': 0, 'creator': 'Someone',
         'creation_date': '2021-01-20T05:02:00+00:00', 'is_user_in_session': False},
        {'has_password': False, 'id': 2, 'state': state, 'name': 'Other', 'num_players': 0, 'creator': 'Someone',
         'creation_date': '2020-01-20T05:02:00+00:00', 'is_user_in_session': False},
        {'has_password': False, 'id': 1, 'state': state, 'name': 'Debug', 'num_players': 0, 'creator': 'Someone',
         'creation_date': '2020-10-02T10:20:00+00:00', 'is_user_in_session': False},
    ]
    if limit == 2:
        expected = expected[:2]

    assert result == expected


def test_create_session(clean_database, preset_manager, default_game_list, mocker):
    # Setup
    user = database.User.create(id=1234, discord_id=5678, name="The Name")
    sio = MagicMock()
    sio.get_current_user.return_value = user

    mock_join: MagicMock = mocker.patch("randovania.server.multiplayer.session_common.join_room")

    # Run
    result = session_api.create_session(sio, "My Room")

    # Assert
    session = database.MultiplayerSession.get(1)

    mock_join.assert_called_once_with(sio, session)

    assert session.name == "My Room"
    assert result == {
        'id': 1,
        'name': 'My Room',
        'state': MultiplayerSessionState.SETUP.value,
        'users_list': [{'admin': True, 'id': 1234, 'name': 'The Name', 'worlds': {}}],
        'worlds': [],
        'game_details': None,
        'generation_in_progress': None,
        'allowed_games': default_game_list,
    }


def test_join_session(mock_emit_session_update: MagicMock,
                      clean_database, default_game_list, mocker):
    # Setup
    user1 = database.User.create(id=1234, name="The Name")
    user2 = database.User.create(id=1235, name="Other Name")
    sio = MagicMock()
    sio.get_current_user.return_value = user1

    mock_join_multiplayer_session: MagicMock = mocker.patch(
        "randovania.server.multiplayer.session_common.join_room")

    session = database.MultiplayerSession.create(name="The Session", password=None, creator=user1)
    database.World.create(session=session, name="World 1", preset="{}",
                          uuid=uuid.UUID('bc82b6cf-df76-4c3d-9ea0-0695c2f7e719'))
    database.MultiplayerMembership.create(user=user2, session=session, row=0, admin=True,
                                          connection_state="Online, Badass")

    # Run
    result = session_api.join_session(sio, 1, None)

    # Assert
    mock_emit_session_update.assert_called_once_with(session)
    assert result == {
        'id': 1,
        'state': MultiplayerSessionState.SETUP.value,
        'name': 'The Session',
        'users_list': [
            {'admin': True, 'id': 1235, 'name': 'Other Name', 'worlds': {}},
            {'admin': False, 'id': 1234, 'name': 'The Name', 'worlds': {}},
        ],
        'worlds': [
            {"id": "bc82b6cf-df76-4c3d-9ea0-0695c2f7e719", "name": "World 1", "preset_raw": "{}"}
        ],
        'game_details': None,
        'generation_in_progress': None,
        'allowed_games': default_game_list,
    }
    mock_join_multiplayer_session.assert_called_once_with(sio, session)


@pytest.mark.parametrize("is_member", [False, True])
@pytest.mark.parametrize("listen", [False, True])
def test_listen_to_session(session_update, mocker: MockerFixture, flask_app, listen, is_member):
    mock_join_room = mocker.patch("randovania.server.multiplayer.session_common.join_room", autospec=True)
    mock_leave_room = mocker.patch("randovania.server.multiplayer.session_common.leave_room", autospec=True)

    if not is_member and listen:
        user = database.User.create(name="Random")
        expectation = pytest.raises(error.NotAuthorizedForActionError)
        membership = None
    else:
        user = database.User.get_by_id(1234)
        membership = database.MultiplayerMembership.get_by_ids(user_id=1234, session_id=session_update)
        expectation = contextlib.nullcontext()

    sio = MagicMock(spec=ServerApp)
    sio.get_current_user.return_value = user

    # Run
    with flask_app.test_request_context(), expectation:
        session_api.listen_to_session(sio, 1, listen)

    # Assert
    if listen and is_member:
        mock_join_room.assert_called_once_with(sio, membership.session)
    else:
        mock_join_room.assert_not_called()

    if not listen:
        mock_leave_room.assert_called_once_with(sio, membership.session.id)
    else:
        mock_leave_room.assert_not_called()


def test_session_request_update(session_update, mocker, flask_app):
    mock_meta_update: MagicMock = mocker.patch(
        "randovania.server.multiplayer.session_common.emit_session_meta_update", autospec=True)
    mock_actions_update: MagicMock = mocker.patch(
        "randovania.server.multiplayer.session_common.emit_session_actions_update", autospec=True)
    mock_audit_update: MagicMock = mocker.patch(
        "randovania.server.multiplayer.session_common.emit_session_audit_update", autospec=True)

    user = database.User.get_by_id(1234)
    sio = MagicMock()
    sio.get_current_user.return_value = user

    # Run
    with flask_app.test_request_context():
        session_api.request_session_update(sio, 1)

    # Assert
    mock_meta_update.assert_called_once_with(session_update)
    mock_actions_update.assert_called_once_with(session_update)
    mock_audit_update.assert_called_once_with(session_update)
