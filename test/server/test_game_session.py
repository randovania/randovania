import json
from unittest.mock import MagicMock, PropertyMock, patch, call

import peewee
import pytest

from randovania.game_description.assignment import PickupTarget
from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.resources.pickup_entry import PickupEntry, ConditionalResources
from randovania.interface_common.cosmetic_patches import CosmeticPatches
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.network_common.admin_actions import SessionAdminUserAction
from randovania.network_common.error import InvalidAction
from randovania.server import game_session, database


def test_setup_app():
    game_session.setup_app(MagicMock())


def test_list_game_sessions(clean_database):
    # Setup
    database.GameSession.create(name="Debug", num_teams=1)
    database.GameSession.create(name="Other", num_teams=2)
    # Run
    result = game_session.list_game_sessions(MagicMock())
    # Assert
    assert result == [
        {'has_password': False, 'id': 1, 'in_game': False, 'name': 'Debug', 'num_players': 0},
        {'has_password': False, 'id': 2, 'in_game': False, 'name': 'Other', 'num_players': 0},
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
    assert result == {
        'id': 1,
        'in_game': False,
        'name': 'My Room',
        'players': [{'admin': True, 'id': 1234, 'name': 'The Name', 'row': 0, 'is_observer': False}],
        'presets': [preset_manager.default_preset.as_json],
        'actions': [],
        'seed_hash': None,
        'spoiler': None,
        'word_hash': None,
    }


@patch("randovania.server.game_session._emit_session_update", autospec=True)
def test_join_game_session(mock_emit_session_update: MagicMock,
                           clean_database):
    # Setup
    user1 = database.User.create(id=1234, name="The Name")
    user2 = database.User.create(id=1235, name="Other Name")
    sio = MagicMock()
    sio.get_current_user.return_value = user1

    session = database.GameSession.create(name="The Session", password=None)
    database.GameSessionPreset.create(session=session, row=0, preset="{}")
    database.GameSessionMembership.create(user=user2, session=session, row=0, is_observer=False, admin=True)

    # Run
    result = game_session.join_game_session(sio, 1, None)

    # Assert
    mock_emit_session_update.assert_called_once_with(session)
    assert result == {
        'id': 1,
        'in_game': False,
        'name': 'The Session',
        'players': [
            {'admin': True, 'id': 1235, 'name': 'Other Name', 'row': 0, 'is_observer': False},
            {'admin': False, 'id': 1234, 'name': 'The Name', 'row': 0, 'is_observer': True},
        ],
        'actions': [],
        'presets': [{}],
        'seed_hash': None,
        'spoiler': None,
        'word_hash': None
    }


def test_game_session_request_pickups_missing_membership(clean_database):
    with pytest.raises(peewee.DoesNotExist):
        game_session.game_session_request_pickups(MagicMock(), 1)


def test_game_session_request_pickups_not_in_game(flask_app, clean_database):
    # Setup
    user = database.User.create(id=1234, discord_id=5678, name="The Name")
    session = database.GameSession.create(name="Debug")
    database.GameSessionMembership.create(
        user=user, session=session,
        row=0, is_observer=False, admin=False)

    sio = MagicMock()
    sio.get_current_user.return_value = user

    # Run
    result = game_session.game_session_request_pickups(sio, 1)

    # Assert
    assert result == []


@pytest.fixture(name="two_player_session")
def two_player_session_fixture(clean_database):
    user1 = database.User.create(id=1234, name="The Name")
    user2 = database.User.create(id=1235, name="Other Name")

    session = database.GameSession.create(id=1, name="Debug", in_game=True)
    database.GameSessionPreset.create(session=session, row=0, preset="{}")
    database.GameSessionPreset.create(session=session, row=1, preset="{}")

    database.GameSessionMembership.create(user=user1, session=session, row=0, is_observer=False, admin=False)
    database.GameSessionMembership.create(user=user2, session=session, row=1, is_observer=False, admin=False)
    database.GameSessionTeamAction.create(session=session, provider_row=1, provider_location_index=0, receiver_row=0)

    return session


@patch("randovania.server.game_session._get_pickup_target", autospec=True)
@patch("randovania.server.game_session._get_resource_database", autospec=True)
@patch("randovania.server.database.GameSession.layout_description", new_callable=PropertyMock)
def test_game_session_request_pickups_one_action(mock_session_description: PropertyMock,
                                                 mock_get_resource_database: MagicMock,
                                                 mock_get_pickup_target: MagicMock,
                                                 flask_app, two_player_session, echoes_resource_database):
    # Setup
    sio = MagicMock()
    sio.get_current_user.return_value = database.User.get_by_id(1234)

    pickup = PickupEntry("A", 1, ItemCategory.TEMPLE_KEY,
                         (
                             ConditionalResources(None, None, ((echoes_resource_database.item[0], 1),)),
                         ))
    mock_get_pickup_target.return_value = PickupTarget(pickup=pickup, player=0)
    mock_get_resource_database.return_value = echoes_resource_database

    # Run
    result = game_session.game_session_request_pickups(sio, 1)

    # Assert
    mock_get_resource_database.assert_called_once_with(mock_session_description.return_value, 0)
    mock_get_pickup_target.assert_called_once_with(mock_session_description.return_value, 1, 0)
    assert result == [{'message': 'Received A from Other Name', 'pickup': '0pth(AO'}]


@patch("flask_socketio.emit", autospec=True)
@patch("randovania.server.game_session._get_pickup_target", autospec=True)
@patch("randovania.server.game_session._get_resource_database", autospec=True)
@patch("randovania.server.database.GameSession.layout_description", new_callable=PropertyMock)
def test_game_session_collect_pickup_for_self(mock_session_description: PropertyMock,
                                              mock_get_resource_database: MagicMock,
                                              mock_get_pickup_target: MagicMock,
                                              mock_emit: MagicMock,
                                              flask_app, two_player_session, echoes_resource_database):
    sio = MagicMock()
    sio.get_current_user.return_value = database.User.get_by_id(1234)

    pickup = PickupEntry("A", 1, ItemCategory.TEMPLE_KEY,
                         (
                             ConditionalResources(None, None, ((echoes_resource_database.item[0], 1),)),
                         ))
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
    mock_emit: MagicMock = mocker.patch("flask_socketio.emit", autospec=True)
    mock_get_pickup_target: MagicMock = mocker.patch("randovania.server.game_session._get_pickup_target", autospec=True)
    mock_session_description: PropertyMock = mocker.patch("randovania.server.database.GameSession.layout_description",
                                                          new_callable=PropertyMock)
    mock_emit_session_update: MagicMock = mocker.patch("randovania.server.game_session._emit_session_update",
                                                       autospec=True)

    sio = MagicMock()
    sio.get_current_user.return_value = database.User.get_by_id(1234)
    mock_get_pickup_target.return_value = PickupTarget(MagicMock(), 1)

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
        mock_emit.assert_not_called()
        mock_emit_session_update.assert_not_called()
    else:
        mock_emit.assert_called_once_with("game_has_update", {"session": 1, "row": 1, },
                                          room=f"game-session-1-1235")
        mock_emit_session_update.assert_called_once_with(database.GameSession.get(id=1))


@pytest.mark.parametrize("is_observer", [False, True])
def test_game_session_admin_player_switch_is_observer(clean_database, flask_app, mocker, is_observer):
    mock_emit_session_update: MagicMock = mocker.patch("randovania.server.game_session._emit_session_update",
                                                       autospec=True)
    user1 = database.User.create(id=1234, name="The Name")
    session = database.GameSession.create(id=1, name="Debug", in_game=True)
    database.GameSessionPreset.create(session=session, row=0, preset="{}")
    database.GameSessionMembership.create(user=user1, session=session, row=0, is_observer=is_observer, admin=False)
    sio = MagicMock()
    sio.get_current_user.return_value = user1

    # Run
    with flask_app.test_request_context():
        game_session.game_session_admin_player(sio, 1, 1234, SessionAdminUserAction.SWITCH_IS_OBSERVER.value, None)

    # Assert
    membership = database.GameSessionMembership.get(user=user1, session=session, row=0)
    assert membership.is_observer != is_observer
    mock_emit_session_update.assert_called_once_with(database.GameSession.get(id=1))


@pytest.mark.parametrize("offset", [-1, 1])
def test_game_session_admin_player_move(clean_database, flask_app, mocker, offset: int):
    mock_emit_session_update: MagicMock = mocker.patch("randovania.server.game_session._emit_session_update",
                                                       autospec=True)
    user1 = database.User.create(id=1234, name="The Name")
    session = database.GameSession.create(id=1, name="Debug", in_game=True)
    database.GameSessionPreset.create(session=session, row=0, preset="{}")
    database.GameSessionPreset.create(session=session, row=1, preset="{}")
    database.GameSessionPreset.create(session=session, row=2, preset="{}")
    database.GameSessionMembership.create(user=user1, session=session, row=1, is_observer=False, admin=False)
    sio = MagicMock()
    sio.get_current_user.return_value = user1

    # Run
    with flask_app.test_request_context():
        game_session.game_session_admin_player(sio, 1, 1234, "move", offset)

    # Assert
    membership = database.GameSessionMembership.get(user=user1, session=session)
    assert membership.row == 1 + offset
    mock_emit_session_update.assert_called_once_with(database.GameSession.get(id=1))


@patch("randovania.games.prime.patcher_file.create_patcher_file", autospec=True)
@patch("randovania.server.database.GameSession.layout_description", new_callable=PropertyMock)
def test_game_session_admin_player_patcher_file(mock_layout_description: PropertyMock,
                                                mock_create_patcher_file: MagicMock,
                                                clean_database):
    user1 = database.User.create(id=1234, name="The Name")
    user2 = database.User.create(id=1235, name="Brother")
    session = database.GameSession.create(id=1, name="Debug", in_game=True)
    database.GameSessionPreset.create(session=session, row=0, preset="{}")
    database.GameSessionPreset.create(session=session, row=1, preset="{}")
    database.GameSessionPreset.create(session=session, row=2, preset="{}")
    database.GameSessionMembership.create(user=user1, session=session, row=2, is_observer=False, admin=False)
    database.GameSessionMembership.create(user=user2, session=session, row=1, is_observer=False, admin=False)
    sio = MagicMock()
    sio.get_current_user.return_value = user1

    cosmetic = CosmeticPatches(open_map=False)

    # Run
    result = game_session.game_session_admin_player(sio, 1, 1234, "create_patcher_file", cosmetic.as_json)

    # Assert
    mock_create_patcher_file.assert_called_once_with(
        mock_layout_description.return_value,
        PlayersConfiguration(2, {
            0: "Player 1",
            1: "Brother",
            2: "The Name",
        }),
        cosmetic
    )
    assert result is mock_create_patcher_file.return_value


@patch("randovania.server.game_session._emit_session_update")
def test_game_session_admin_session_create_row(mock_emit_session_update: MagicMock,
                                               clean_database, preset_manager):
    user1 = database.User.create(id=1234, name="The Name")
    session = database.GameSession.create(id=1, name="Debug", in_game=False)
    database.GameSessionMembership.create(user=user1, session=session, row=2, is_observer=True, admin=True)
    sio = MagicMock()
    sio.get_current_user.return_value = user1

    # Run
    game_session.game_session_admin_session(sio, 1, "create_row", preset_manager.default_preset.as_json)

    # Assert
    mock_emit_session_update.assert_called_once_with(session)
    assert database.GameSession.get_by_id(1).num_rows == 1


@patch("randovania.server.game_session._emit_session_update")
def test_game_session_admin_session_change_row(mock_emit_session_update: MagicMock,
                                               clean_database, preset_manager):
    user1 = database.User.create(id=1234, name="The Name")
    session = database.GameSession.create(id=1, name="Debug", in_game=False)
    database.GameSessionPreset.create(session=session, row=0, preset="{}")
    database.GameSessionPreset.create(session=session, row=1, preset="{}")
    database.GameSessionMembership.create(user=user1, session=session, row=2, is_observer=True, admin=True)
    sio = MagicMock()
    sio.get_current_user.return_value = user1

    # Run
    game_session.game_session_admin_session(sio, 1, "change_row", (1, preset_manager.default_preset.as_json))

    # Assert
    mock_emit_session_update.assert_called_once_with(session)
    new_preset_row = database.GameSessionPreset.get(database.GameSessionPreset.session == session,
                                                    database.GameSessionPreset.row == 1)
    assert json.loads(new_preset_row.preset) == preset_manager.default_preset.as_json


@patch("randovania.server.game_session._emit_session_update")
def test_game_session_admin_session_delete_row(mock_emit_session_update: MagicMock,
                                               clean_database, preset_manager):
    user1 = database.User.create(id=1234, name="The Name")
    session = database.GameSession.create(id=1, name="Debug", in_game=False)
    database.GameSessionPreset.create(session=session, row=0, preset="{}")
    database.GameSessionPreset.create(session=session, row=1, preset="{}")
    database.GameSessionMembership.create(user=user1, session=session, row=2, is_observer=True, admin=True)
    sio = MagicMock()
    sio.get_current_user.return_value = user1

    # Run
    game_session.game_session_admin_session(sio, 1, "delete_row", 1)

    # Assert
    mock_emit_session_update.assert_called_once_with(session)
    assert database.GameSession.get_by_id(1).num_rows == 1


@patch("randovania.layout.layout_description.LayoutDescription.from_json_dict")
@patch("randovania.server.game_session._emit_session_update", autospec=True)
def test_game_session_admin_session_change_layout_description(mock_emit_session_update: MagicMock,
                                                              mock_from_json_dict: MagicMock,
                                                              clean_database, preset_manager):
    preset_as_json = json.dumps(preset_manager.default_preset.as_json)
    user1 = database.User.create(id=1234, name="The Name")
    session = database.GameSession.create(id=1, name="Debug", in_game=False)
    database.GameSessionPreset.create(session=session, row=0, preset=preset_as_json)
    database.GameSessionPreset.create(session=session, row=1, preset=preset_as_json)
    database.GameSessionMembership.create(user=user1, session=session, row=2, is_observer=True, admin=True)
    sio = MagicMock()
    sio.get_current_user.return_value = user1
    layout_description = mock_from_json_dict.return_value
    layout_description.as_json = "some_json_string"
    layout_description.permalink.presets = {i: preset_manager.default_preset for i in (0, 1)}

    # Run
    game_session.game_session_admin_session(sio, 1, "change_layout_description", "layout_description_json")

    # Assert
    mock_emit_session_update.assert_called_once_with(session)
    assert database.GameSession.get_by_id(1).layout_description_json == '"some_json_string"'


@patch("randovania.server.database.GameSession.layout_description", new_callable=PropertyMock)
@patch("randovania.server.game_session._emit_session_update", autospec=True)
def test_game_session_admin_session_download_layout_description(mock_emit_session_update: MagicMock,
                                                                mock_layout_description: PropertyMock,
                                                                clean_database, ):
    user1 = database.User.create(id=1234, name="The Name")
    session = database.GameSession.create(id=1, name="Debug", in_game=False,
                                          layout_description_json="layout_description_json")
    database.GameSessionMembership.create(user=user1, session=session, row=2, is_observer=True, admin=False)
    sio = MagicMock()
    sio.get_current_user.return_value = user1

    # Run
    result = game_session.game_session_admin_session(sio, 1, "download_layout_description", None)

    # Assert
    mock_emit_session_update.assert_not_called()
    mock_layout_description.assert_called_once()
    assert result == database.GameSession.get_by_id(1).layout_description_json


@patch("randovania.server.database.GameSession.layout_description", new_callable=PropertyMock)
@patch("randovania.server.game_session._emit_session_update", autospec=True)
def test_game_session_admin_session_download_layout_description_no_spoiler(mock_emit_session_update: MagicMock,
                                                                           mock_layout_description: PropertyMock,
                                                                           clean_database, ):
    user1 = database.User.create(id=1234, name="The Name")
    session = database.GameSession.create(id=1, name="Debug", in_game=False,
                                          layout_description_json="layout_description_json")
    database.GameSessionMembership.create(user=user1, session=session, row=2, is_observer=True, admin=False)
    sio = MagicMock()
    sio.get_current_user.return_value = user1
    mock_layout_description.return_value.permalink.spoiler = False

    # Run
    with pytest.raises(InvalidAction):
        game_session.game_session_admin_session(sio, 1, "download_layout_description", None)

    # Assert
    mock_emit_session_update.assert_not_called()
    mock_layout_description.assert_called_once()


@patch("randovania.server.database.GameSession.layout_description", new_callable=PropertyMock)
@patch("randovania.server.game_session._emit_session_update")
def test_game_session_admin_session_start_session(mock_emit_session_update: MagicMock,
                                                  mock_session_description: PropertyMock,
                                                  clean_database, preset_manager):
    user1 = database.User.create(id=1234, name="The Name")
    session = database.GameSession.create(id=1, name="Debug", in_game=False, layout_description_json="{}")
    database.GameSessionPreset.create(session=session, row=0, preset="{}")
    database.GameSessionMembership.create(user=user1, session=session, row=0, is_observer=False, admin=True)
    sio = MagicMock()
    sio.get_current_user.return_value = user1

    # Run
    game_session.game_session_admin_session(sio, 1, "start_session", None)

    # Assert
    mock_emit_session_update.assert_called_once_with(session)
    assert database.GameSession.get_by_id(1).in_game
