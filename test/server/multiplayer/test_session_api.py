from __future__ import annotations

import contextlib
import datetime
import uuid
from typing import TYPE_CHECKING

import pytest

from randovania.network_common import error
from randovania.network_common.session_visibility import MultiplayerSessionVisibility
from randovania.server import database
from randovania.server.multiplayer import session_api

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


@pytest.mark.parametrize("limit", [None, 2, 3])
async def test_list_sessions(clean_database, mock_sa, limit):
    # Setup
    utc = datetime.UTC
    someone = database.User.create(name="Someone")
    other = database.User.create(name="Other")
    s1 = database.MultiplayerSession.create(
        name="Debug",
        num_teams=1,
        creator=someone,
        password="Foo",
        creation_date=datetime.datetime(2020, 10, 2, 10, 20, tzinfo=utc),
    )
    s2 = database.MultiplayerSession.create(
        name="Other", num_teams=2, creator=someone, creation_date=datetime.datetime(2020, 1, 20, 5, 2, tzinfo=utc)
    )
    s3 = database.MultiplayerSession.create(
        name="Third", num_teams=2, creator=someone, creation_date=datetime.datetime(2021, 1, 20, 5, 2, tzinfo=utc)
    )

    database.MultiplayerMembership.create(
        user=someone, session=s1, join_date=datetime.datetime(2021, 1, 20, 5, 2, tzinfo=utc)
    )
    database.MultiplayerMembership.create(
        user=someone, session=s3, join_date=datetime.datetime(2022, 1, 20, 5, 2, tzinfo=utc)
    )
    database.MultiplayerMembership.create(
        user=other, session=s2, join_date=datetime.datetime(2021, 1, 20, 5, 2, tzinfo=utc)
    )
    database.MultiplayerMembership.create(
        user=other, session=s3, join_date=datetime.datetime(2022, 1, 20, 5, 2, tzinfo=utc)
    )

    world1_s1 = database.World.create(session=s1, name="Foobar World 1", preset="I'm a dummy")
    database.WorldUserAssociation.create(world=world1_s1, user=someone)
    world2_s1 = database.World.create(session=s1, name="Foobar World 2", preset="I'm a dummy")
    database.WorldUserAssociation.create(world=world2_s1, user=someone)
    world1_s2 = database.World.create(session=s2, name="Foobar World 1", preset="I'm a dummy")
    database.WorldUserAssociation.create(world=world1_s2, user=someone)

    visibility = MultiplayerSessionVisibility.VISIBLE.value
    mock_sa.get_current_user.return_value = someone

    # Run
    result = await session_api.list_sessions(mock_sa, "TheSid", limit)

    # Assert
    expected = [
        {
            "has_password": False,
            "id": 3,
            "visibility": visibility,
            "name": "Third",
            "num_users": 2,
            "creator": "Someone",
            "num_worlds": 0,
            "creation_date": "2021-01-20T05:02:00+00:00",
            "is_user_in_session": True,
            "join_date": "2022-01-20T05:02:00+00:00",
        },
        {
            "has_password": False,
            "id": 2,
            "visibility": visibility,
            "name": "Other",
            "num_users": 1,
            "creator": "Someone",
            "num_worlds": 1,
            "creation_date": "2020-01-20T05:02:00+00:00",
            "is_user_in_session": False,
            "join_date": "2021-01-20T05:02:00+00:00",
        },
        {
            "has_password": True,
            "id": 1,
            "visibility": visibility,
            "name": "Debug",
            "num_users": 1,
            "creator": "Someone",
            "num_worlds": 2,
            "creation_date": "2020-10-02T10:20:00+00:00",
            "is_user_in_session": True,
            "join_date": "2021-01-20T05:02:00+00:00",
        },
    ]
    if limit == 2:
        expected = expected[:2]

    assert result == expected


async def test_create_session(clean_database, preset_manager, default_game_list, mock_sa, mocker: MockerFixture):
    # Setup
    user = database.User.create(id=1234, discord_id=5678, name="The Name")

    mock_sa.get_current_user.return_value = user

    mock_join = mocker.patch("randovania.server.multiplayer.session_common.join_room")

    # Run
    result = await session_api.create_session(mock_sa, "TheSid", "My Room")

    # Assert
    session = database.MultiplayerSession.get(1)

    mock_join.assert_awaited_once_with(mock_sa, "TheSid", session)

    assert session.name == "My Room"
    assert result == {
        "id": 1,
        "name": "My Room",
        "visibility": MultiplayerSessionVisibility.VISIBLE.value,
        "users_list": [{"admin": True, "ready": False, "id": 1234, "name": "The Name", "worlds": {}}],
        "worlds": [],
        "game_details": None,
        "generation_in_progress": None,
        "allowed_games": default_game_list,
        "allow_coop": False,
        "allow_everyone_claim_world": False,
    }


async def test_join_session(
    mock_emit_session_update, mock_sa, clean_database, default_game_list, mocker: MockerFixture
):
    # Setup
    user1 = database.User.create(id=1234, name="The Name")
    user2 = database.User.create(id=1235, name="Other Name")

    mock_sa.get_current_user.return_value = user1

    mock_join_multiplayer_session = mocker.patch("randovania.server.multiplayer.session_common.join_room")

    session = database.MultiplayerSession.create(name="The Session", password=None, creator=user1)
    database.World.create(
        session=session, name="World 1", preset="{}", uuid=uuid.UUID("bc82b6cf-df76-4c3d-9ea0-0695c2f7e719")
    )
    database.MultiplayerMembership.create(
        user=user2, session=session, row=0, admin=True, connection_state="Online, Badass"
    )

    # Run
    result = await session_api.join_session(mock_sa, "TheSid", 1, None)

    # Assert
    mock_emit_session_update.assert_awaited_once_with(mock_sa, session)
    assert result == {
        "id": 1,
        "visibility": MultiplayerSessionVisibility.VISIBLE.value,
        "name": "The Session",
        "users_list": [
            {"admin": True, "ready": False, "id": 1235, "name": "Other Name", "worlds": {}},
            {"admin": False, "ready": False, "id": 1234, "name": "The Name", "worlds": {}},
        ],
        "worlds": [
            {
                "id": "bc82b6cf-df76-4c3d-9ea0-0695c2f7e719",
                "name": "World 1",
                "preset_raw": "{}",
                "has_been_beaten": False,
            }
        ],
        "game_details": None,
        "generation_in_progress": None,
        "allowed_games": default_game_list,
        "allow_coop": False,
        "allow_everyone_claim_world": False,
    }
    mock_join_multiplayer_session.assert_awaited_once_with(mock_sa, "TheSid", session)


@pytest.mark.parametrize("is_member", [False, True])
@pytest.mark.parametrize("listen", [False, True])
async def test_listen_to_session(session_update, mocker: MockerFixture, mock_sa, listen, is_member):
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

    mock_sa.get_current_user.return_value = user

    # Run
    with expectation:
        await session_api.listen_to_session(mock_sa, "TheSid", 1, listen)

    # Assert
    if listen and is_member:
        mock_join_room.assert_awaited_once_with(mock_sa, "TheSid", membership.session)
    else:
        mock_join_room.assert_not_called()

    if not listen:
        mock_leave_room.assert_awaited_once_with(mock_sa, "TheSid", membership.session.id)
    else:
        mock_leave_room.assert_not_called()


async def test_session_request_update(session_update, mocker: MockerFixture, mock_sa):
    mock_meta_update = mocker.patch(
        "randovania.server.multiplayer.session_common.emit_session_meta_update", autospec=True
    )
    mock_actions_update = mocker.patch(
        "randovania.server.multiplayer.session_common.emit_session_actions_update", autospec=True
    )
    mock_audit_update = mocker.patch(
        "randovania.server.multiplayer.session_common.emit_session_audit_update", autospec=True
    )

    user = database.User.get_by_id(1234)

    mock_sa.get_current_user.return_value = user

    # Run
    await session_api.request_session_update(mock_sa, "TheSid", 1)

    # Assert
    mock_meta_update.assert_awaited_once_with(mock_sa, session_update)
    mock_actions_update.assert_awaited_once_with(mock_sa, session_update)
    mock_audit_update.assert_awaited_once_with(mock_sa, session_update)
