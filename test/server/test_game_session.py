import contextlib
import dataclasses
import datetime
import json
from unittest.mock import MagicMock, PropertyMock, patch, call

import peewee
import pytest

from randovania.game_description.assignment import PickupTarget
from randovania.game_description.resources.pickup_entry import PickupEntry, PickupModel
from randovania.games.binary_data import convert_to_raw_python
from randovania.games.game import RandovaniaGame
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.layout.preset_migration import VersionedPreset
from randovania.layout.prime2.echoes_cosmetic_patches import EchoesCosmeticPatches
from randovania.network_common.admin_actions import SessionAdminUserAction, SessionAdminGlobalAction
from randovania.network_common.binary_formats import BinaryGameSessionEntry, BinaryGameSessionActions, \
    BinaryGameSessionAuditLog
from randovania.network_common.error import InvalidAction
from randovania.network_common.session_state import GameSessionState
from randovania.server import game_session, database


@pytest.fixture(name="mock_emit_session_update")
def _mock_emit_session_update(mocker) -> MagicMock:
    return mocker.patch("randovania.server.game_session._emit_session_meta_update", autospec=True)


@pytest.fixture(name="mock_audit")
def _mock_audit(mocker) -> MagicMock:
    return mocker.patch("randovania.server.game_session._add_audit_entry", autospec=True)


def test_setup_app():
    game_session.setup_app(MagicMock())


def test_game_session_defaults_to_now(clean_database):
    someone = database.User.create(name="Someone")
    database.GameSession.create(name="Debug", num_teams=1, creator=someone)

    session: database.GameSession = database.GameSession.get_by_id(1)
    assert (datetime.datetime.now(datetime.timezone.utc) - session.creation_datetime) < datetime.timedelta(seconds=5)


def test_list_game_sessions(clean_database):
    # Setup
    utc = datetime.timezone.utc
    someone = database.User.create(name="Someone")
    database.GameSession.create(name="Debug", num_teams=1, creator=someone,
                                creation_date=datetime.datetime(2020, 10, 2, 10, 20, tzinfo=utc))
    database.GameSession.create(name="Other", num_teams=2, creator=someone,
                                creation_date=datetime.datetime(2020, 1, 20, 5, 2, tzinfo=utc))
    state = GameSessionState.SETUP.value

    # Run
    result = game_session.list_game_sessions(MagicMock())

    # Assert
    assert result == [
        {'has_password': False, 'id': 1, 'state': state, 'name': 'Debug', 'num_players': 0, 'creator': 'Someone',
         'creation_date': '2020-10-02T10:20:00+00:00'},
        {'has_password': False, 'id': 2, 'state': state, 'name': 'Other', 'num_players': 0, 'creator': 'Someone',
         'creation_date': '2020-01-20T05:02:00+00:00'},
    ]


def test_create_game_session(clean_database, preset_manager):
    # Setup
    user = database.User.create(id=1234, discord_id=5678, name="The Name")
    sio = MagicMock()
    sio.get_current_user.return_value = user

    # Run
    result = game_session.create_game_session(sio, "My Room")

    # Assert
    session = database.GameSession.get(1)
    assert session.name == "My Room"
    assert convert_to_raw_python(BinaryGameSessionEntry.parse(result)) == {
        'id': 1,
        'state': GameSessionState.SETUP.value,
        'name': 'My Room',
        'players': [{'admin': True, 'id': 1234, 'name': 'The Name', 'row': 0,
                     'connection_state': 'Online, Unknown'}],
        'presets': [json.dumps(preset_manager.default_preset.as_json)],
        'game_details': None,
        'generation_in_progress': None,
        'allowed_games': ['prime1', 'prime2'],
    }


def test_join_game_session(mock_emit_session_update: MagicMock,
                           clean_database):
    # Setup
    user1 = database.User.create(id=1234, name="The Name")
    user2 = database.User.create(id=1235, name="Other Name")
    sio = MagicMock()
    sio.get_current_user.return_value = user1

    session = database.GameSession.create(name="The Session", password=None, creator=user1)
    database.GameSessionPreset.create(session=session, row=0, preset="{}")
    database.GameSessionMembership.create(user=user2, session=session, row=0, admin=True,
                                          connection_state="Online, Badass")

    # Run
    result = game_session.join_game_session(sio, 1, None)

    # Assert
    mock_emit_session_update.assert_called_once_with(session)
    assert convert_to_raw_python(BinaryGameSessionEntry.parse(result)) == {
        'id': 1,
        'state': GameSessionState.SETUP.value,
        'name': 'The Session',
        'players': [
            {'admin': True, 'id': 1235, 'name': 'Other Name', 'row': 0,
             'connection_state': 'Online, Badass'},
            {'admin': False, 'id': 1234, 'name': 'The Name', 'row': None,
             'connection_state': 'Online, Unknown'},
        ],
        'presets': ["{}"],
        'game_details': None,
        'generation_in_progress': None,
        'allowed_games': ['prime1', 'prime2'],
    }


def test_game_session_request_pickups_not_in_game(flask_app, clean_database):
    # Setup
    user = database.User.create(id=1234, discord_id=5678, name="The Name")
    session = database.GameSession.create(name="Debug", creator=user)
    membership = database.GameSessionMembership.create(user=user, session=session, row=0, admin=False)

    sio = MagicMock()
    sio.get_current_user.return_value = user

    # Run
    with pytest.raises(RuntimeError, match="Unable to emit pickups during SETUP"):
        game_session._emit_game_session_pickups_update(sio, membership)


def test_game_session_request_pickups_observer(flask_app, clean_database):
    # Setup
    user = database.User.create(id=1234, discord_id=5678, name="The Name")
    session = database.GameSession.create(name="Debug", creator=user, state=GameSessionState.IN_PROGRESS)
    membership = database.GameSessionMembership.create(user=user, session=session, row=None, admin=False)

    sio = MagicMock()
    sio.get_current_user.return_value = user

    # Run
    with pytest.raises(RuntimeError, match="Unable to emit pickups for observers"):
        game_session._emit_game_session_pickups_update(sio, membership)


@pytest.fixture(name="two_player_session")
def two_player_session_fixture(clean_database):
    user1 = database.User.create(id=1234, name="The Name")
    user2 = database.User.create(id=1235, name="Other Name")

    session = database.GameSession.create(id=1, name="Debug", state=GameSessionState.IN_PROGRESS, creator=user1)
    database.GameSessionPreset.create(session=session, row=0, preset="{}")
    database.GameSessionPreset.create(session=session, row=1, preset="{}")

    database.GameSessionMembership.create(user=user1, session=session, row=0, admin=False)
    database.GameSessionMembership.create(user=user2, session=session, row=1, admin=False)
    database.GameSessionTeamAction.create(session=session, provider_row=1, provider_location_index=0, receiver_row=0)

    return session


@patch("randovania.server.game_session._get_pickup_target", autospec=True)
@patch("randovania.server.game_session._get_resource_database", autospec=True)
@patch("randovania.server.database.GameSession.layout_description", new_callable=PropertyMock)
def test_game_session_request_pickups_one_action(mock_session_description: PropertyMock,
                                                 mock_get_resource_database: MagicMock,
                                                 mock_get_pickup_target: MagicMock,
                                                 flask_app, two_player_session, generic_item_category, echoes_resource_database, mocker):
    # Setup
    mock_emit: MagicMock = mocker.patch("flask_socketio.emit")

    sio = MagicMock()
    sio.get_current_user.return_value = database.User.get_by_id(1234)
    membership = database.GameSessionMembership.get(user=database.User.get_by_id(1234), session=two_player_session)

    pickup = PickupEntry("A", PickupModel(echoes_resource_database.game_enum, "AmmoModel"),
                         generic_item_category, generic_item_category,
                         progression=((echoes_resource_database.item[0], 1),))
    mock_get_pickup_target.return_value = PickupTarget(pickup=pickup, player=0)
    mock_get_resource_database.return_value = echoes_resource_database

    # Run
    game_session._emit_game_session_pickups_update(sio, membership)

    # Uncomment this to encode the data once again and get the new bytefield if it changed for some reason 
#    from randovania.server.game_session import _base64_encode_pickup
#    new_data = _base64_encode_pickup(pickup, echoes_resource_database)
#    print(new_data)

    # Assert
    mock_get_resource_database.assert_called_once_with(mock_session_description.return_value, 0)
    mock_get_pickup_target.assert_called_once_with(mock_session_description.return_value, 1, 0)
    mock_emit.assert_called_once_with(
        "game_session_pickups_update",
        {
            "game": "prime2",
            "pickups": [{'provider_name': 'Other Name', 'pickup': 'C@fSK*4Fga_C{97Z0xPfu1zd+0;96GGPyLdkR-Y?wvZvPx-zr3xjeQO;t7BqTb$e(SlU^dSy>1gT^U<QZ0xPfu1zd+0;96GGPyLdkR-Y?wvZvPx-zr3xjeQO;t7BqTb$e(SlU^dSy>1gT^U<K1RMY'}]
        },
        room=f"game-session-1-1234"
    )


@patch("flask_socketio.emit", autospec=True)
@patch("randovania.server.game_session._get_pickup_target", autospec=True)
@patch("randovania.server.game_session._get_resource_database", autospec=True)
@patch("randovania.server.database.GameSession.layout_description", new_callable=PropertyMock)
def test_game_session_collect_pickup_for_self(mock_session_description: PropertyMock,
                                              mock_get_resource_database: MagicMock,
                                              mock_get_pickup_target: MagicMock,
                                              mock_emit: MagicMock,
                                              flask_app, two_player_session, generic_item_category, echoes_resource_database):
    sio = MagicMock()
    sio.get_current_user.return_value = database.User.get_by_id(1234)

    pickup = PickupEntry("A", 1, generic_item_category, generic_item_category,
                         progression=((echoes_resource_database.item[0], 1),))
    mock_get_resource_database.return_value = echoes_resource_database
    mock_get_pickup_target.return_value = PickupTarget(pickup, 0)

    # Run
    with flask_app.test_request_context():
        result = game_session.game_session_collect_locations(sio, 1, (0,))

    # Assert
    assert result is None
    mock_emit.assert_not_called()
    mock_get_pickup_target.assert_called_once_with(mock_session_description.return_value, 0, 0)
    with pytest.raises(peewee.DoesNotExist):
        database.GameSessionTeamAction.get(session=two_player_session, provider_row=0,
                                           provider_location_index=0)


@patch("flask_socketio.emit", autospec=True)
@patch("randovania.server.game_session._get_pickup_target", autospec=True)
@patch("randovania.server.database.GameSession.layout_description", new_callable=PropertyMock)
def test_game_session_collect_pickup_etm(mock_session_description: PropertyMock,
                                         mock_get_pickup_target: MagicMock,
                                         mock_emit: MagicMock,
                                         flask_app, two_player_session, echoes_resource_database):
    sio = MagicMock()
    sio.get_current_user.return_value = database.User.get_by_id(1234)

    mock_get_pickup_target.return_value = None

    # Run
    with flask_app.test_request_context():
        result = game_session.game_session_collect_locations(sio, 1, (0,))

    # Assert
    assert result is None
    mock_emit.assert_not_called()
    mock_get_pickup_target.assert_called_once_with(mock_session_description.return_value, 0, 0)
    with pytest.raises(peewee.DoesNotExist):
        database.GameSessionTeamAction.get(session=two_player_session, provider_row=0,
                                           provider_location_index=0)


@pytest.mark.parametrize(("locations_to_collect", "exists"), [
    ((0,), ()),
    ((0,), (0,)),
    ((0, 1), ()),
    ((0, 1), (0,)),
    ((0, 1), (0, 1)),
])
def test_game_session_collect_pickup_other(flask_app, two_player_session, echoes_resource_database,
                                           locations_to_collect, exists, mocker):
    mock_emit_pickups_update: MagicMock = mocker.patch(
        "randovania.server.game_session._emit_game_session_pickups_update", autospec=True)
    mock_get_pickup_target: MagicMock = mocker.patch("randovania.server.game_session._get_pickup_target", autospec=True)
    mock_session_description: PropertyMock = mocker.patch("randovania.server.database.GameSession.layout_description",
                                                          new_callable=PropertyMock)
    mock_emit_session_update = mocker.patch("randovania.server.game_session._emit_session_actions_update",
                                            autospec=True)

    sio = MagicMock()
    sio.get_current_user.return_value = database.User.get_by_id(1234)
    mock_get_pickup_target.return_value = PickupTarget(MagicMock(), 1)
    membership = database.GameSessionMembership.get_by_session_position(two_player_session, row=1)

    for existing_id in exists:
        database.GameSessionTeamAction.create(session=two_player_session, provider_row=0,
                                              provider_location_index=existing_id, receiver_row=0)

    # Run
    with flask_app.test_request_context():
        result = game_session.game_session_collect_locations(sio, 1, locations_to_collect)

    # Assert
    assert result is None
    mock_get_pickup_target.assert_has_calls([
        call(mock_session_description.return_value, 0, location)
        for location in locations_to_collect
    ])
    for location in locations_to_collect:
        database.GameSessionTeamAction.get(session=two_player_session, provider_row=0,
                                           provider_location_index=location)
    if exists == locations_to_collect:
        mock_emit_pickups_update.assert_not_called()
        mock_emit_session_update.assert_not_called()
    else:
        mock_emit_pickups_update.assert_called_once_with(sio, membership)
        mock_emit_session_update.assert_called_once_with(database.GameSession.get(id=1))


@pytest.mark.parametrize("is_observer", [False, True])
def test_game_session_admin_player_switch_is_observer(clean_database, flask_app, mock_emit_session_update, is_observer):
    user1 = database.User.create(id=1234, name="The Name")
    session = database.GameSession.create(id=1, name="Debug", state=GameSessionState.IN_PROGRESS, creator=user1)
    database.GameSessionPreset.create(session=session, row=0, preset="{}")
    database.GameSessionMembership.create(user=user1, session=session, row=None if is_observer else 0, admin=False)
    sio = MagicMock()
    sio.get_current_user.return_value = user1

    # Run
    with flask_app.test_request_context():
        game_session.game_session_admin_player(sio, 1, 1234, SessionAdminUserAction.SWITCH_IS_OBSERVER.value, None)

    # Assert
    membership = database.GameSessionMembership.get(user=user1, session=session)
    assert membership.is_observer != is_observer
    if is_observer:
        assert membership.row == 0
    mock_emit_session_update.assert_called_once_with(database.GameSession.get(id=1))


def test_game_session_admin_player_include_in_session(clean_database, flask_app, mock_emit_session_update):
    users = [
        database.User.create(id=1234 + 1000 * i, name=f"The {i}")
        for i in range(4)
    ]
    session = database.GameSession.create(id=1, name="Debug", state=GameSessionState.IN_PROGRESS, creator=users[0])
    for i in range(4):
        database.GameSessionPreset.create(session=session, row=i, preset="{}")

    database.GameSessionMembership.create(user=users[0], session=session, row=0, admin=True)
    database.GameSessionMembership.create(user=users[1], session=session, row=2, admin=False)
    database.GameSessionMembership.create(user=users[2], session=session, row=1, admin=False)
    database.GameSessionMembership.create(user=users[3], session=session, row=None, admin=False)
    sio = MagicMock()
    sio.get_current_user.return_value = users[0]

    # Run
    with flask_app.test_request_context():
        game_session.game_session_admin_player(sio, 1, 4234, SessionAdminUserAction.SWITCH_IS_OBSERVER.value, None)

    # Assert
    membership = database.GameSessionMembership.get(user=users[3], session=session)
    assert not membership.is_observer
    assert membership.row == 3
    mock_emit_session_update.assert_called_once_with(database.GameSession.get(id=1))


def test_game_session_admin_kick_last(clean_database, flask_app, mocker, mock_audit):
    mock_emit = mocker.patch("flask_socketio.emit")

    user = database.User.create(id=1234, discord_id=5678, name="The Name")
    sio = MagicMock()
    sio.get_current_user.return_value = user
    game_session.create_game_session(sio, "My Room")
    session = database.GameSession.get_by_id(1)
    database.GameSessionTeamAction.create(session=session, provider_row=0, provider_location_index=0, receiver_row=0,
                                          time=datetime.datetime(2020, 5, 2, 10, 20, tzinfo=datetime.timezone.utc))

    # Run
    with flask_app.test_request_context():
        game_session.game_session_admin_player(sio, 1, 1234, SessionAdminUserAction.KICK.value, None)

    # Assert
    for table in [database.GameSession, database.GameSessionPreset,
                  database.GameSessionMembership, database.GameSessionTeamAction]:
        assert list(table.select()) == []
    assert database.User.get_by_id(1234) == user

    mock_emit.assert_called_once_with(
        "game_session_meta_update",
        BinaryGameSessionEntry.build({'id': 1, 'name': 'My Room', 'state': 'setup', 'players': [], 'presets': [],
                                      'game_details': None, 'generation_in_progress': None,
                                      'allowed_games': ['prime1', 'prime2'], }),
        room='game-session-1')
    mock_audit.assert_called_once_with(sio, session, "Left session")


@pytest.mark.parametrize("offset", [-1, 1])
def test_game_session_admin_player_move(clean_database, flask_app, mock_emit_session_update, offset: int):
    user1 = database.User.create(id=1234, name="The Name")
    session = database.GameSession.create(id=1, name="Debug", state=GameSessionState.IN_PROGRESS, creator=user1)
    database.GameSessionPreset.create(session=session, row=0, preset="{}")
    database.GameSessionPreset.create(session=session, row=1, preset="{}")
    database.GameSessionPreset.create(session=session, row=2, preset="{}")
    database.GameSessionMembership.create(user=user1, session=session, row=1, admin=False)
    sio = MagicMock()
    sio.get_current_user.return_value = user1

    # Run
    with flask_app.test_request_context():
        game_session.game_session_admin_player(sio, 1, 1234, "move", offset)

    # Assert
    membership = database.GameSessionMembership.get(user=user1, session=session)
    assert membership.row == 1 + offset
    mock_emit_session_update.assert_called_once_with(database.GameSession.get(id=1))


@patch("randovania.server.database.GameSession.layout_description", new_callable=PropertyMock)
def test_game_session_admin_player_patcher_file(mock_layout_description: PropertyMock,
                                                flask_app, mock_audit,
                                                clean_database):
    user1 = database.User.create(id=1234, name="The Name")
    user2 = database.User.create(id=1235, name="Brother")
    session = database.GameSession.create(id=1, name="Debug", state=GameSessionState.IN_PROGRESS, creator=user1)
    database.GameSessionPreset.create(session=session, row=0, preset="{}")
    database.GameSessionPreset.create(session=session, row=1, preset="{}")
    database.GameSessionPreset.create(session=session, row=2, preset="{}")
    database.GameSessionMembership.create(user=user1, session=session, row=2, admin=False)
    database.GameSessionMembership.create(user=user2, session=session, row=1, admin=False)
    sio = MagicMock()
    sio.get_current_user.return_value = user1
    patcher = sio.patcher_provider.patcher_for_game.return_value
    mock_layout_description.return_value.permalink.get_preset.return_value.game = RandovaniaGame.METROID_PRIME_ECHOES

    cosmetic = EchoesCosmeticPatches(open_map=False)

    # Run
    with flask_app.test_request_context():
        result = game_session.game_session_admin_player(sio, 1, 1234, "create_patcher_file", cosmetic.as_json)

    # Assert
    mock_layout_description.return_value.permalink.get_preset.assert_called_once_with(2)
    sio.patcher_provider.patcher_for_game.assert_called_once_with(RandovaniaGame.METROID_PRIME_ECHOES)
    patcher.create_patch_data.assert_called_once_with(
        mock_layout_description.return_value,
        PlayersConfiguration(2, {
            0: "Player 1",
            1: "Brother",
            2: "The Name",
        }),
        cosmetic
    )
    assert result is patcher.create_patch_data.return_value
    mock_audit.assert_called_once_with(sio, session, "Made an ISO for row 3")


def test_game_session_admin_session_delete_session(mock_emit_session_update: MagicMock, flask_app, clean_database):
    user1 = database.User.create(id=1234, name="The Name")
    session = database.GameSession.create(id=1, name="Debug", state=GameSessionState.SETUP, creator=user1)
    database.GameSessionMembership.create(user=user1, session=session, row=None, admin=True)
    sio = MagicMock()
    sio.get_current_user.return_value = user1

    # Run
    with flask_app.test_request_context():
        game_session.game_session_admin_session(sio, 1, SessionAdminGlobalAction.DELETE_SESSION.value, None)

    # Assert
    mock_emit_session_update.assert_called_once_with(session)
    assert list(database.GameSession.select()) == []


def test_game_session_admin_session_create_row(mock_emit_session_update: MagicMock,
                                               clean_database, flask_app, preset_manager):
    user1 = database.User.create(id=1234, name="The Name")
    session = database.GameSession.create(id=1, name="Debug", state=GameSessionState.SETUP, creator=user1)
    database.GameSessionMembership.create(user=user1, session=session, row=None, admin=True)
    sio = MagicMock()
    sio.get_current_user.return_value = user1

    # Run
    with flask_app.test_request_context():
        game_session.game_session_admin_session(sio, 1, "create_row", preset_manager.default_preset.as_json)

    # Assert
    mock_emit_session_update.assert_called_once_with(session)
    assert database.GameSession.get_by_id(1).num_rows == 1


def test_game_session_admin_session_change_row(mock_emit_session_update: MagicMock,
                                               clean_database, flask_app, preset_manager):
    user1 = database.User.create(id=1234, name="The Name")
    session = database.GameSession.create(id=1, name="Debug", state=GameSessionState.SETUP, creator=user1)
    database.GameSessionPreset.create(session=session, row=0, preset="{}")
    database.GameSessionPreset.create(session=session, row=1, preset="{}")
    database.GameSessionMembership.create(user=user1, session=session, row=None, admin=True)
    sio = MagicMock()
    sio.get_current_user.return_value = user1

    # Make sure the preset is using the latest version
    preset_manager.default_preset.ensure_converted()

    # Run
    with flask_app.test_request_context():
        game_session.game_session_admin_session(sio, 1, SessionAdminGlobalAction.CHANGE_ROW.value,
                                                (1, preset_manager.default_preset.as_json))

    # Assert
    mock_emit_session_update.assert_called_once_with(session)
    new_preset_row = database.GameSessionPreset.get(database.GameSessionPreset.session == session,
                                                    database.GameSessionPreset.row == 1)
    assert json.loads(new_preset_row.preset) == preset_manager.default_preset.as_json


def test_game_session_admin_session_delete_row(mock_emit_session_update: MagicMock,
                                               clean_database, flask_app, preset_manager):
    user1 = database.User.create(id=1234, name="The Name")
    session = database.GameSession.create(id=1, name="Debug", state=GameSessionState.SETUP, creator=user1)
    database.GameSessionPreset.create(session=session, row=0, preset="{}")
    database.GameSessionPreset.create(session=session, row=1, preset="{}")
    database.GameSessionMembership.create(user=user1, session=session, row=None, admin=True)
    sio = MagicMock()
    sio.get_current_user.return_value = user1

    # Run
    with flask_app.test_request_context():
        game_session.game_session_admin_session(sio, 1, SessionAdminGlobalAction.DELETE_ROW.value, 1)

    # Assert
    mock_emit_session_update.assert_called_once_with(session)
    assert database.GameSession.get_by_id(1).num_rows == 1


@pytest.mark.parametrize("not_last_row", [False, True])
def test_game_session_admin_session_delete_row_invalid(mock_emit_session_update,
                                                       clean_database, preset_manager,
                                                       flask_app, not_last_row):
    user1 = database.User.create(id=1234, name="The Name")
    session = database.GameSession.create(id=1, name="Debug", state=GameSessionState.SETUP, creator=user1)
    database.GameSessionPreset.create(session=session, row=0, preset="{}")
    database.GameSessionMembership.create(user=user1, session=session, row=None, admin=True)
    sio = MagicMock()
    sio.get_current_user.return_value = user1
    if not_last_row:
        database.GameSessionPreset.create(session=session, row=1, preset="{}")
        expected_message = "Can only delete the last row"
        expected_num_rows = 2
    else:
        expected_message = "Can't delete row when there's only one"
        expected_num_rows = 1

    # Run
    with pytest.raises(InvalidAction) as e, flask_app.test_request_context():
        game_session.game_session_admin_session(sio, 1, SessionAdminGlobalAction.DELETE_ROW.value, 0)

    # Assert
    assert e.value.message == expected_message
    mock_emit_session_update.assert_not_called()
    assert database.GameSession.get_by_id(1).num_rows == expected_num_rows


@pytest.mark.parametrize("case", ["to_false", "to_true_free", "to_true_busy"])
def test_game_session_admin_session_update_layout_generation(mock_emit_session_update: MagicMock,
                                                             clean_database, flask_app, case):
    user1 = database.User.create(id=1234, name="The Name")
    user2 = database.User.create(id=1235, name="Other")
    session = database.GameSession.create(id=1, name="Debug", state=GameSessionState.SETUP, creator=user1,
                                          generation_in_progress=user2 if case == "to_true_busy" else None)
    database.GameSessionMembership.create(user=user1, session=session, row=None, admin=True)
    sio = MagicMock()
    sio.get_current_user.return_value = user1

    if case == "to_true_busy":
        expectation = pytest.raises(InvalidAction, match="Generation already in progress by Other.")
        expected_user = user2
    else:
        expectation = contextlib.nullcontext()
        if case == "to_false":
            expected_user = None
        else:
            expected_user = user1

    # Run
    with expectation, flask_app.test_request_context():
        game_session.game_session_admin_session(sio, 1, SessionAdminGlobalAction.UPDATE_LAYOUT_GENERATION.value,
                                                case != "to_false")

    # Assert
    if case == "to_true_busy":
        mock_emit_session_update.assert_not_called()
    else:
        mock_emit_session_update.assert_called_once_with(session)
    assert database.GameSession.get_by_id(1).generation_in_progress == expected_user


def test_game_session_admin_session_change_layout_description(clean_database, preset_manager, mock_emit_session_update,
                                                              mocker, flask_app, mock_audit):
    mock_verify_no_layout_description = mocker.patch("randovania.server.game_session._verify_no_layout_description",
                                                     autospec=True)
    mock_from_json_dict: MagicMock = mocker.patch(
        "randovania.layout.layout_description.LayoutDescription.from_json_dict")

    preset_as_json = json.dumps(preset_manager.default_preset.as_json)
    user1 = database.User.create(id=1234, name="The Name")
    session = database.GameSession.create(id=1, name="Debug", state=GameSessionState.SETUP, creator=user1,
                                          generation_in_progress=user1)
    database.GameSessionPreset.create(session=session, row=0, preset=preset_as_json)
    database.GameSessionPreset.create(session=session, row=1, preset=preset_as_json)
    database.GameSessionMembership.create(user=user1, session=session, row=None, admin=True)

    new_preset = preset_manager.default_preset.get_preset()
    new_preset = dataclasses.replace(new_preset,
                                     configuration=dataclasses.replace(new_preset.configuration,
                                                                       menu_mod=False))

    sio = MagicMock()
    sio.get_current_user.return_value = user1
    layout_description = mock_from_json_dict.return_value
    layout_description.as_json = "some_json_string"
    layout_description.permalink.player_count = 2
    layout_description.permalink.presets = {i: new_preset for i in (0, 1)}
    layout_description.shareable_word_hash = "Hash Words"

    # Run
    with flask_app.test_request_context():
        game_session.game_session_admin_session(sio, 1, SessionAdminGlobalAction.CHANGE_LAYOUT_DESCRIPTION.value,
                                                "layout_description_json")

    # Assert
    mock_emit_session_update.assert_called_once_with(session)
    mock_audit.assert_called_once_with(sio, session, "Set game to Hash Words")
    mock_verify_no_layout_description.assert_called_once_with(session)
    assert database.GameSession.get_by_id(1).layout_description_json == '"some_json_string"'
    assert database.GameSession.get_by_id(1).generation_in_progress is None

    new_session = database.GameSession.get_by_id(1)
    new_json = json.dumps(VersionedPreset.with_preset(new_preset).as_json)
    assert [preset.preset for preset in new_session.presets] == [new_json] * 2


def test_game_session_admin_session_remove_layout_description(mock_emit_session_update: MagicMock, clean_database,
                                                              flask_app, mock_audit):
    user1 = database.User.create(id=1234, name="The Name")
    session = database.GameSession.create(id=1, name="Debug", state=GameSessionState.SETUP, creator=user1,
                                          generation_in_progress=user1,
                                          layout_description_json="layout_description_json")
    database.GameSessionMembership.create(user=user1, session=session, row=None, admin=True)
    sio = MagicMock()
    sio.get_current_user.return_value = user1

    # Run
    with flask_app.test_request_context():
        game_session.game_session_admin_session(sio, 1, SessionAdminGlobalAction.CHANGE_LAYOUT_DESCRIPTION.value,
                                                None)

    # Assert
    mock_emit_session_update.assert_called_once_with(session)
    mock_audit.assert_called_once_with(sio, session, "Removed generated game")
    assert database.GameSession.get_by_id(1).layout_description_json is None
    assert database.GameSession.get_by_id(1).generation_in_progress is None


@pytest.mark.parametrize("other_user", [False, True])
def test_game_session_admin_session_change_layout_description_invalid(mock_emit_session_update: MagicMock,
                                                                      clean_database, other_user, flask_app):
    user1 = database.User.create(id=1234, name="The Name")
    user2 = database.User.create(id=1235, name="Other")
    session = database.GameSession.create(id=1, name="Debug", state=GameSessionState.SETUP, creator=user1,
                                          generation_in_progress=user2 if other_user else None)
    database.GameSessionMembership.create(user=user1, session=session, row=None, admin=True)
    sio = MagicMock()
    sio.get_current_user.return_value = user1

    if other_user:
        expected_message = "Waiting for a layout from Other."
    else:
        expected_message = "Not waiting for a layout."

    # Run
    with pytest.raises(InvalidAction, match=expected_message), flask_app.test_request_context():
        game_session.game_session_admin_session(sio, 1, SessionAdminGlobalAction.CHANGE_LAYOUT_DESCRIPTION.value,
                                                "layout_description_json")

    # Assert
    mock_emit_session_update.assert_not_called()
    assert database.GameSession.get_by_id(1).layout_description_json is None


@patch("randovania.server.database.GameSession.layout_description", new_callable=PropertyMock)
def test_game_session_admin_session_download_layout_description(mock_layout_description: PropertyMock, flask_app,
                                                                clean_database, mock_emit_session_update, mock_audit):
    user1 = database.User.create(id=1234, name="The Name")
    session = database.GameSession.create(id=1, name="Debug", state=GameSessionState.SETUP, creator=user1,
                                          layout_description_json="layout_description_json")
    database.GameSessionMembership.create(user=user1, session=session, row=None, admin=False)
    sio = MagicMock()
    sio.get_current_user.return_value = user1

    # Run
    with flask_app.test_request_context():
        result = game_session.game_session_admin_session(sio, 1,
                                                         SessionAdminGlobalAction.DOWNLOAD_LAYOUT_DESCRIPTION.value,
                                                         None)

    # Assert
    mock_emit_session_update.assert_not_called()
    mock_audit.assert_called_once_with(sio, session, "Requested the spoiler log")
    mock_layout_description.assert_called_once()
    assert result == database.GameSession.get_by_id(1).layout_description_json


@patch("randovania.server.database.GameSession.layout_description", new_callable=PropertyMock)
def test_game_session_admin_session_download_layout_description_no_spoiler(mock_layout_description: PropertyMock,
                                                                           clean_database, mock_emit_session_update,
                                                                           flask_app):
    user1 = database.User.create(id=1234, name="The Name")
    session = database.GameSession.create(id=1, name="Debug", state=GameSessionState.SETUP, creator=user1,
                                          layout_description_json="layout_description_json")
    database.GameSessionMembership.create(user=user1, session=session, row=None, admin=False)
    sio = MagicMock()
    sio.get_current_user.return_value = user1
    mock_layout_description.return_value.permalink.spoiler = False

    # Run
    with pytest.raises(InvalidAction), flask_app.test_request_context():
        game_session.game_session_admin_session(sio, 1, SessionAdminGlobalAction.DOWNLOAD_LAYOUT_DESCRIPTION.value,
                                                None)

    # Assert
    mock_emit_session_update.assert_not_called()
    mock_layout_description.assert_called_once()


@patch("randovania.server.database.GameSession.layout_description", new_callable=PropertyMock)
def test_game_session_admin_session_start_session(mock_session_description: PropertyMock,
                                                  mock_emit_session_update,
                                                  clean_database, preset_manager,
                                                  flask_app, mock_audit):
    user1 = database.User.create(id=1234, name="The Name")
    session = database.GameSession.create(id=1, name="Debug", state=GameSessionState.SETUP, creator=user1,
                                          layout_description_json="{}")
    database.GameSessionPreset.create(session=session, row=0, preset="{}")
    database.GameSessionMembership.create(user=user1, session=session, row=0, admin=True)
    sio = MagicMock()
    sio.get_current_user.return_value = user1

    # Run
    with flask_app.test_request_context():
        game_session.game_session_admin_session(sio, 1, SessionAdminGlobalAction.START_SESSION.value, None)

    # Assert
    mock_emit_session_update.assert_called_once_with(session)
    mock_audit.assert_called_once_with(sio, session, "Started session")
    assert database.GameSession.get_by_id(1).state == GameSessionState.IN_PROGRESS


@pytest.mark.parametrize("starting_state", [GameSessionState.SETUP, GameSessionState.IN_PROGRESS,
                                            GameSessionState.FINISHED])
def test_game_session_admin_session_finish_session(clean_database, mock_emit_session_update, starting_state,
                                                   flask_app, mock_audit):
    user1 = database.User.create(id=1234, name="The Name")
    session = database.GameSession.create(id=1, name="Debug", state=starting_state, creator=user1)
    database.GameSessionMembership.create(user=user1, session=session, row=0, admin=True)
    sio = MagicMock()
    sio.get_current_user.return_value = user1
    if starting_state != GameSessionState.IN_PROGRESS:
        expectation = pytest.raises(InvalidAction, match="Invalid Action: Session is not in progress")
    else:
        expectation = contextlib.nullcontext()

    # Run
    with expectation, flask_app.test_request_context():
        game_session.game_session_admin_session(sio, 1, SessionAdminGlobalAction.FINISH_SESSION.value, None)

    # Assert
    if starting_state != GameSessionState.IN_PROGRESS:
        mock_emit_session_update.assert_not_called()
        mock_audit.assert_not_called()
        assert database.GameSession.get_by_id(1).state == starting_state
    else:
        mock_emit_session_update.assert_called_once_with(session)
        mock_audit.assert_called_once_with(sio, session, "Finished session")
        assert database.GameSession.get_by_id(1).state == GameSessionState.FINISHED


def test_game_session_admin_session_reset_session(clean_database, flask_app):
    user1 = database.User.create(id=1234, name="The Name")
    session = database.GameSession.create(id=1, name="Debug", state=GameSessionState.SETUP, creator=user1)
    database.GameSessionMembership.create(user=user1, session=session, row=0, admin=True)
    sio = MagicMock()
    sio.get_current_user.return_value = user1

    # Run
    with pytest.raises(InvalidAction), flask_app.test_request_context():
        game_session.game_session_admin_session(sio, 1, SessionAdminGlobalAction.RESET_SESSION.value, None)


def test_game_session_admin_session_change_password(clean_database, mock_emit_session_update, flask_app, mock_audit):
    user1 = database.User.create(id=1234, name="The Name")
    session = database.GameSession.create(id=1, name="Debug", state=GameSessionState.SETUP, creator=user1)
    database.GameSessionMembership.create(user=user1, session=session, row=0, admin=True)
    sio = MagicMock()
    sio.get_current_user.return_value = user1
    expected_password = 'da92cfbc5e318c64e33dc1b0501e5db214cea0e2a5cecabf90269f32f8eaa15f'

    # Run
    with flask_app.test_request_context():
        game_session.game_session_admin_session(sio, 1, SessionAdminGlobalAction.CHANGE_PASSWORD.value, "the_password")

    # Assert
    mock_emit_session_update.assert_called_once_with(session)
    mock_audit.assert_called_once_with(sio, session, "Changed password")
    assert database.GameSession.get_by_id(1).password == expected_password


def test_change_row_missing_arguments(flask_app):
    with pytest.raises(InvalidAction), flask_app.test_request_context():
        game_session._change_row(MagicMock(), MagicMock(), (5,))


def test_verify_in_setup(clean_database, flask_app):
    user1 = database.User.create(id=1234, name="The Name")
    session = database.GameSession.create(id=1, name="Debug", state=GameSessionState.IN_PROGRESS, creator=user1,
                                          layout_description_json="{}")

    with pytest.raises(InvalidAction), flask_app.test_request_context():
        game_session._verify_in_setup(session)


def test_verify_no_layout_description(clean_database, flask_app):
    user1 = database.User.create(id=1234, name="The Name")
    session = database.GameSession.create(id=1, name="Debug", state=GameSessionState.IN_PROGRESS, creator=user1,
                                          layout_description_json="{}")

    with pytest.raises(InvalidAction), flask_app.test_request_context():
        game_session._verify_in_setup(session)


@pytest.fixture(name="session_update")
def session_update_fixture(clean_database, mocker):
    mock_layout = mocker.patch("randovania.server.database.GameSession.layout_description", new_callable=PropertyMock)
    target = mock_layout.return_value.all_patches.__getitem__.return_value.pickup_assignment.__getitem__.return_value
    target.pickup.name = "The Pickup"
    mock_layout.return_value.shareable_word_hash = "Words of O-Lir"
    mock_layout.return_value.shareable_hash = "ABCDEFG"
    mock_layout.return_value.permalink.spoiler = True
    mock_layout.return_value.permalink.as_base64_str = "<permalink>"
    mock_layout.return_value.permalink.get_preset.return_value.game = RandovaniaGame.METROID_PRIME_ECHOES

    user1 = database.User.create(id=1234, name="The Name")
    user2 = database.User.create(id=1235, name="Other")
    session = database.GameSession.create(id=1, name="Debug", state=GameSessionState.IN_PROGRESS, creator=user1,
                                          layout_description_json="{}")
    database.GameSessionMembership.create(user=user1, session=session, row=0, admin=True,
                                          connection_state="Something")
    database.GameSessionMembership.create(user=user2, session=session, row=1, admin=False,
                                          connection_state="Game")
    database.GameSessionTeamAction.create(session=session, provider_row=1, provider_location_index=0, receiver_row=0,
                                          time=datetime.datetime(2020, 5, 2, 10, 20, tzinfo=datetime.timezone.utc))

    return session


def test_emit_session_meta_update(session_update, mocker):
    mock_emit: MagicMock = mocker.patch("flask_socketio.emit")

    session_json = {
        "id": 1,
        "name": "Debug",
        "state": GameSessionState.IN_PROGRESS.value,
        "players": [
            {
                "id": 1234,
                "name": "The Name",
                "row": 0,
                "admin": True,
                'connection_state': 'Something',
            },
            {
                "id": 1235,
                "name": "Other",
                "row": 1,
                "admin": False,
                'connection_state': 'Game',
            },
        ],
        "presets": [],
        "game_details": {
            "spoiler": True,
            "word_hash": "Words of O-Lir",
            "seed_hash": "ABCDEFG",
            "permalink": "<permalink>",
        },
        "generation_in_progress": None,
        'allowed_games': ['prime1', 'prime2'],
    }

    # Run
    game_session._emit_session_meta_update(session_update)

    # Assert
    mock_emit.assert_called_once_with(
        "game_session_meta_update",
        BinaryGameSessionEntry.build(session_json),
        room=f"game-session-{session_update.id}"
    )


def test_emit_session_actions_update(session_update, mocker):
    mock_emit: MagicMock = mocker.patch("flask_socketio.emit")

    actions = [
        {
            "location": 0,
            "pickup": "The Pickup",
            "provider": "Other",
            "provider_row": 1,
            "receiver": "The Name",
            "time": "2020-05-02T10:20:00+00:00",
        }
    ]

    # Run
    game_session._emit_session_actions_update(session_update)

    # Assert
    mock_emit.assert_called_once_with(
        "game_session_actions_update",
        BinaryGameSessionActions.build(actions),
        room=f"game-session-{session_update.id}"
    )


def test_emit_session_audit_update(session_update, mocker):
    mock_emit: MagicMock = mocker.patch("flask_socketio.emit")

    database.GameSessionAudit.create(session=session_update, user=1234, message="Did something",
                                     time=datetime.datetime(2020, 5, 2, 10, 20, tzinfo=datetime.timezone.utc))
    database.GameSessionAudit.create(session=session_update, user=1235, message="Did something else",
                                     time=datetime.datetime(2020, 5, 3, 10, 20, tzinfo=datetime.timezone.utc))

    audit_log = [
        {"user": "The Name", "message": "Did something", "time": "2020-05-02T10:20:00+00:00"},
        {"user": "Other", "message": "Did something else", "time": "2020-05-03T10:20:00+00:00"},
    ]

    # Run
    game_session._emit_session_audit_update(session_update)

    # Assert
    mock_emit.assert_called_once_with(
        "game_session_audit_update",
        BinaryGameSessionAuditLog.build(audit_log),
        room=f"game-session-{session_update.id}"
    )


def test_game_session_request_update(session_update, mocker, flask_app):
    mock_meta_update: MagicMock = mocker.patch(
        "randovania.server.game_session._emit_session_meta_update", autospec=True)
    mock_actions_update: MagicMock = mocker.patch(
        "randovania.server.game_session._emit_session_actions_update", autospec=True)
    mock_pickups_update: MagicMock = mocker.patch(
        "randovania.server.game_session._emit_game_session_pickups_update", autospec=True)
    mock_audit_update: MagicMock = mocker.patch(
        "randovania.server.game_session._emit_session_audit_update", autospec=True)

    user = database.User.get_by_id(1234)
    sio = MagicMock()
    sio.get_current_user.return_value = user
    membership = database.GameSessionMembership.get(user=user, session=session_update)

    # Run
    with flask_app.test_request_context():
        game_session.game_session_request_update(sio, 1)

    # Assert
    mock_meta_update.assert_called_once_with(session_update)
    mock_actions_update.assert_called_once_with(session_update)
    mock_pickups_update.assert_called_once_with(sio, membership)
    mock_audit_update.assert_called_once_with(session_update)
