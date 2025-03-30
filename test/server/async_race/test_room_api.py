import contextlib
import datetime
from unittest.mock import ANY, MagicMock

import pytest
import pytest_mock

from randovania.layout.layout_description import LayoutDescription
from randovania.network_common import error
from randovania.network_common.async_race_room import (
    AsyncRaceEntryData,
    AsyncRaceRoomUserStatus,
    AsyncRaceSettings,
    RaceRoomLeaderboard,
    RaceRoomLeaderboardEntry,
)
from randovania.network_common.audit import AuditEntry
from randovania.network_common.game_details import GameDetails
from randovania.network_common.session_visibility import MultiplayerSessionVisibility
from randovania.network_common.user import RandovaniaUser
from randovania.server.async_race import room_api
from randovania.server.database import AsyncRaceAuditEntry, AsyncRaceEntry, AsyncRaceEntryPause, AsyncRaceRoom, User
from randovania.server.server_app import ServerApp


def test_verify_authorization_no_password(simple_room):
    # Setup
    sa = MagicMock()

    # Run
    room_api._verify_authorization(sa, simple_room, "AuthToken")

    # Assert
    sa.decrypt_dict.assert_not_called()


def test_verify_authorization_password_valid(simple_room):
    # Setup
    sa = MagicMock()
    sa.decrypt_dict.return_value = {
        "room_id": simple_room.id,
        "time": datetime.datetime.now().timestamp(),
    }
    simple_room.password = "SomePassword"

    # Run
    room_api._verify_authorization(sa, simple_room, "AuthToken")

    # Assert
    sa.decrypt_dict.assert_called_once_with("AuthToken")


def test_verify_authorization_password_wrong_room(simple_room):
    # Setup
    sa = MagicMock()
    sa.decrypt_dict.return_value = {
        "room_id": 1234,
        "time": datetime.datetime.now().timestamp(),
    }
    simple_room.password = "SomePassword"

    # Run
    with pytest.raises(error.NotAuthorizedForActionError):
        room_api._verify_authorization(sa, simple_room, "AuthToken")

    # Assert
    sa.decrypt_dict.assert_called_once_with("AuthToken")


def test_verify_authorization_token_too_old(simple_room):
    # Setup
    sa = MagicMock()
    sa.decrypt_dict.return_value = {
        "room_id": simple_room.id,
        "time": 0,
    }
    simple_room.password = "SomePassword"

    # Run
    with pytest.raises(error.NotAuthorizedForActionError):
        room_api._verify_authorization(sa, simple_room, "AuthToken")

    # Assert
    sa.decrypt_dict.assert_called_once_with("AuthToken")


def test_verify_authorization_unexpected_error(simple_room):
    # Setup
    sa = MagicMock()
    sa.decrypt_dict.return_value = {}
    simple_room.password = "SomePassword"

    # Run
    with pytest.raises(error.NotAuthorizedForActionError):
        room_api._verify_authorization(sa, simple_room, "AuthToken")

    # Assert
    sa.decrypt_dict.assert_called_once_with("AuthToken")


def test_list_rooms(simple_room, mocker: pytest_mock.MockFixture):
    # Setup
    sa = MagicMock()
    mocker.patch(
        "randovania.server.lib.datetime_now",
        return_value=datetime.datetime(year=2020, month=5, day=12, tzinfo=datetime.UTC),
    )

    # Run
    results = room_api.list_rooms(sa, None)

    # Assert
    assert results == [
        {
            "id": simple_room.id,
            "name": simple_room.name,
            "games": ["prime2"],
            "has_password": False,
            "creator": simple_room.creator.name,
            "creation_date": "2020-05-02T10:20:00+00:00",
            "start_date": "2020-05-10T00:00:00+00:00",
            "end_date": "2020-06-10T00:00:00+00:00",
            "visibility": "visible",
            "race_status": "active",
        }
    ]


def test_create_room(clean_database, test_files_dir, mocker: pytest_mock.MockFixture):
    # Setup
    mocker.patch(
        "randovania.server.lib.datetime_now",
        return_value=datetime.datetime(year=2019, month=5, day=12, tzinfo=datetime.UTC),
    )

    user1 = User.create(id=1234, name="The Name")
    sa = MagicMock()
    sa.get_current_user.return_value = user1

    description = LayoutDescription.from_file(test_files_dir.joinpath("log_files", "prime2_seed_b.rdvgame"))
    layout_bin = description.as_binary()
    settings_json = AsyncRaceSettings(
        name="TheRoom",
        password=None,
        start_date=datetime.datetime(year=2020, month=1, day=1, tzinfo=datetime.UTC),
        end_date=datetime.datetime(year=2021, month=1, day=1, tzinfo=datetime.UTC),
        visibility=MultiplayerSessionVisibility.VISIBLE,
        allow_pause=True,
    ).as_json

    # Run
    result = room_api.create_room(sa, layout_bin, settings_json)

    # Assert
    assert result == {
        "allow_pause": True,
        "auth_token": ANY,
        "creator": "The Name",
        "creation_date": "2019-05-12T00:00:00+00:00",
        "start_date": "2020-01-01T00:00:00+00:00",
        "end_date": "2021-01-01T00:00:00+00:00",
        "game_details": GameDetails.from_layout(description).as_json,
        "id": 1,
        "is_admin": True,
        "name": "TheRoom",
        "presets_raw": [ANY],
        "race_status": "scheduled",
        "self_status": "not-member",
        "visibility": "visible",
    }


def test_change_room_settings_wrong_user(simple_room, mocker: pytest_mock.MockFixture):
    # Setup
    mocker.patch(
        "randovania.server.lib.datetime_now",
        return_value=datetime.datetime(year=2020, month=5, day=12, tzinfo=datetime.UTC),
    )

    sa = MagicMock()
    sa.get_current_user.return_value = User.get_by_id(1235)

    settings_json = AsyncRaceSettings(
        name="TheRoom",
        password=None,
        start_date=datetime.datetime(year=2020, month=6, day=1, tzinfo=datetime.UTC),
        end_date=datetime.datetime(year=2020, month=7, day=1, tzinfo=datetime.UTC),
        visibility=MultiplayerSessionVisibility.VISIBLE,
        allow_pause=True,
    ).as_json

    # Run
    with pytest.raises(error.NotAuthorizedForActionError):
        room_api.change_room_settings(sa, simple_room.id, settings_json)


def test_change_room_settings_back_in_time(simple_room, mocker: pytest_mock.MockFixture):
    # Setup
    mocker.patch(
        "randovania.server.lib.datetime_now",
        return_value=datetime.datetime(year=2020, month=5, day=12, tzinfo=datetime.UTC),
    )

    # creation_date = datetime.datetime(2020, 5, 2, 10, 20, tzinfo=datetime.UTC),
    # start_date = datetime.datetime(2020, 5, 10, 0, 0, tzinfo=datetime.UTC),
    # end_date = datetime.datetime(2020, 6, 10, 0, 0, tzinfo=datetime.UTC),

    sa = MagicMock()
    sa.get_current_user.return_value = User.get_by_id(1234)

    settings_json = AsyncRaceSettings(
        name="TheRoom",
        password=None,
        start_date=datetime.datetime(year=2020, month=6, day=1, tzinfo=datetime.UTC),
        end_date=datetime.datetime(year=2020, month=7, day=1, tzinfo=datetime.UTC),
        visibility=MultiplayerSessionVisibility.VISIBLE,
        allow_pause=True,
    ).as_json

    # Run
    with pytest.raises(error.InvalidActionError, match="Can't go back in time for race status"):
        room_api.change_room_settings(sa, simple_room.id, settings_json)


def test_change_room_settings_valid(simple_room, mocker: pytest_mock.MockFixture):
    # Setup
    now = datetime.datetime(year=2019, month=5, day=12, tzinfo=datetime.UTC)
    mocker.patch("randovania.server.lib.datetime_now", return_value=now)

    sa = MagicMock()
    sa.get_current_user.return_value = User.get_by_id(1234)

    settings_json = AsyncRaceSettings(
        name="TheRoom",
        password=None,
        start_date=datetime.datetime(year=2020, month=6, day=1, tzinfo=datetime.UTC),
        end_date=datetime.datetime(year=2020, month=7, day=1, tzinfo=datetime.UTC),
        visibility=MultiplayerSessionVisibility.VISIBLE,
        allow_pause=True,
    ).as_json

    # Run
    result = room_api.change_room_settings(sa, simple_room.id, settings_json)

    # Assert
    assert result == {
        "id": 1,
        "auth_token": ANY,
        "name": "TheRoom",
        "creator": "The Name",
        "creation_date": "2020-05-02T10:20:00+00:00",
        "start_date": "2020-06-01T00:00:00+00:00",
        "end_date": "2020-07-01T00:00:00+00:00",
        "game_details": ANY,
        "is_admin": True,
        "presets_raw": [ANY],
        "race_status": "scheduled",
        "self_status": "not-member",
        "visibility": "visible",
        "allow_pause": True,
    }


@pytest.mark.parametrize("password", [None, "Something"])
def test_get_room_valid_password(simple_room, mocker: pytest_mock.MockFixture, password: str | None):
    # Setup
    now = datetime.datetime(year=2019, month=5, day=12, tzinfo=datetime.UTC)
    mocker.patch("randovania.server.lib.datetime_now", return_value=now)

    simple_room.password = password
    simple_room.save()

    sa = MagicMock()
    sa.get_current_user.return_value = User.get_by_id(1234)

    # Run
    result = room_api.get_room(sa, simple_room.id, password)

    # Assert
    assert result == {
        "id": 1,
        "auth_token": ANY,
        "name": "Debug",
        "creator": "The Name",
        "creation_date": "2020-05-02T10:20:00+00:00",
        "start_date": "2020-05-10T00:00:00+00:00",
        "end_date": "2020-06-10T00:00:00+00:00",
        "game_details": ANY,
        "is_admin": True,
        "presets_raw": [ANY],
        "race_status": "scheduled",
        "self_status": "not-member",
        "visibility": "visible",
        "allow_pause": True,
    }


@pytest.mark.parametrize("has_password", [False, True])
def test_get_room_wrong_password(simple_room, has_password: bool):
    # Setup
    if has_password:
        simple_room.password = "Something"
        used_password = None
    else:
        simple_room.password = None
        used_password = "Something"

    simple_room.save()

    sa = MagicMock()
    sa.get_current_user.return_value = User.get_by_id(1234)

    with pytest.raises(error.WrongPasswordError):
        room_api.get_room(sa, simple_room.id, used_password)


def test_refresh_room(simple_room, mocker: pytest_mock.MockFixture):
    # Setup
    now = datetime.datetime(year=2019, month=5, day=12, tzinfo=datetime.UTC)
    mocker.patch("randovania.server.lib.datetime_now", return_value=now)
    mock_verify = mocker.patch("randovania.server.async_race.room_api._verify_authorization")

    sa = MagicMock()
    sa.get_current_user.return_value = User.get_by_id(1234)

    # Run
    result = room_api.refresh_room(sa, simple_room.id, "AuthTokenx")

    # Assert
    mock_verify.assert_called_once_with(sa, simple_room, "AuthTokenx")
    assert result == {
        "id": 1,
        "auth_token": ANY,
        "name": "Debug",
        "creator": "The Name",
        "creation_date": "2020-05-02T10:20:00+00:00",
        "start_date": "2020-05-10T00:00:00+00:00",
        "end_date": "2020-06-10T00:00:00+00:00",
        "game_details": ANY,
        "is_admin": True,
        "presets_raw": [ANY],
        "race_status": "scheduled",
        "self_status": "not-member",
        "visibility": "visible",
        "allow_pause": True,
    }


def _force_state(entry: AsyncRaceEntry, state: AsyncRaceRoomUserStatus, after_state: AsyncRaceRoomUserStatus) -> None:
    finish_date = datetime.datetime(2020, 5, 12, 0, 0, tzinfo=datetime.UTC)

    match state:
        case AsyncRaceRoomUserStatus.JOINED:
            entry.start_date = None
        case AsyncRaceRoomUserStatus.STARTED:
            pass
        case AsyncRaceRoomUserStatus.PAUSED:
            entry.paused = True
            AsyncRaceEntryPause.create(entry=entry, start=finish_date)
        case AsyncRaceRoomUserStatus.FINISHED:
            entry.finish_date = finish_date
        case AsyncRaceRoomUserStatus.FORFEITED:
            entry.forfeit = True
            if after_state == AsyncRaceRoomUserStatus.FINISHED:
                entry.finish_date = finish_date


VALID_TRANSITIONS = {
    (AsyncRaceRoomUserStatus.JOINED, AsyncRaceRoomUserStatus.STARTED),
    (AsyncRaceRoomUserStatus.STARTED, AsyncRaceRoomUserStatus.JOINED),
    (AsyncRaceRoomUserStatus.STARTED, AsyncRaceRoomUserStatus.PAUSED),
    (AsyncRaceRoomUserStatus.PAUSED, AsyncRaceRoomUserStatus.STARTED),
    (AsyncRaceRoomUserStatus.STARTED, AsyncRaceRoomUserStatus.FINISHED),
    (AsyncRaceRoomUserStatus.FINISHED, AsyncRaceRoomUserStatus.STARTED),
    (AsyncRaceRoomUserStatus.STARTED, AsyncRaceRoomUserStatus.FORFEITED),
    (AsyncRaceRoomUserStatus.FINISHED, AsyncRaceRoomUserStatus.FORFEITED),
    (AsyncRaceRoomUserStatus.FORFEITED, AsyncRaceRoomUserStatus.STARTED),
    (AsyncRaceRoomUserStatus.FORFEITED, AsyncRaceRoomUserStatus.FINISHED),
}


@pytest.mark.parametrize("after_state", list(AsyncRaceRoomUserStatus))
@pytest.mark.parametrize("before_state", list(AsyncRaceRoomUserStatus))
def test_change_state(
    simple_room,
    mocker: pytest_mock.MockFixture,
    before_state,
    after_state,
):
    # Setup
    now = datetime.datetime(year=2021, month=5, day=12, tzinfo=datetime.UTC)
    mocker.patch("randovania.server.lib.datetime_now", return_value=now)

    room = AsyncRaceRoom.get_by_id(1)
    user = User.get_by_id(1235)

    sa = MagicMock(spec=ServerApp)
    sa.get_current_user.return_value = user

    entry = AsyncRaceEntry.entry_for(room, user)
    if before_state == AsyncRaceRoomUserStatus.NOT_MEMBER:
        entry.delete_instance()
    else:
        _force_state(entry, before_state, after_state)
        entry.save()
        assert AsyncRaceEntry.entry_for(room, user).user_status() == before_state

    valid_transition = (before_state, after_state) in VALID_TRANSITIONS
    if valid_transition:
        expectation = contextlib.nullcontext()
        expected_after = after_state
    else:
        if before_state == AsyncRaceRoomUserStatus.NOT_MEMBER:
            expectation = pytest.raises(error.NotAuthorizedForActionError)
        else:
            expectation = pytest.raises(error.InvalidActionError, match="Unsupported state transition")
        expected_after = before_state

    # Run
    with expectation:
        room_api.change_state(sa, room.id, after_state.value)

    # Assert
    if before_state != AsyncRaceRoomUserStatus.NOT_MEMBER:
        assert AsyncRaceEntry.entry_for(room, user).user_status() == expected_after

    if (before_state, after_state) == (AsyncRaceRoomUserStatus.JOINED, AsyncRaceRoomUserStatus.STARTED):
        assert AsyncRaceEntry.entry_for(room, user).start_datetime == now


def test_get_leaderboard_too_early(simple_room, mocker: pytest_mock.MockFixture):
    # Setup
    now = datetime.datetime(year=2019, month=5, day=12, tzinfo=datetime.UTC)
    mocker.patch("randovania.server.lib.datetime_now", return_value=now)

    sa = MagicMock(spec=ServerApp)

    # Run
    with pytest.raises(error.NotAuthorizedForActionError):
        room_api.get_leaderboard(sa, simple_room.id, "")


def test_get_leaderboard(simple_room, mocker: pytest_mock.MockFixture):
    # Setup
    now = datetime.datetime(year=2021, month=5, day=12, tzinfo=datetime.UTC)
    mocker.patch("randovania.server.lib.datetime_now", return_value=now)

    room = AsyncRaceRoom.get_by_id(1)

    user1 = User.get_by_id(1234)
    user2 = User.get_by_id(1235)
    user3 = User.create(id=1236, name="Last Player")

    AsyncRaceEntry.create(
        room=room,
        user=user1,
        join_date=datetime.datetime(2020, 5, 6, 0, 0, tzinfo=datetime.UTC),
        start_date=datetime.datetime(2020, 5, 12, 0, 0, tzinfo=datetime.UTC),
    )

    entry2 = AsyncRaceEntry.entry_for(room, user2)
    entry2.finish_datetime = datetime.datetime(2020, 5, 11, 1, 0, tzinfo=datetime.UTC)
    entry2.save()

    entry3 = AsyncRaceEntry.create(
        room=room,
        user=user3,
        join_date=datetime.datetime(2020, 5, 6, 0, 0, tzinfo=datetime.UTC),
        start_date=datetime.datetime(2020, 5, 13, 0, 0, tzinfo=datetime.UTC),
        finish_date=datetime.datetime(2020, 5, 13, 2, 0, tzinfo=datetime.UTC),
    )
    AsyncRaceEntryPause.create(
        entry=entry3,
        start=datetime.datetime(2020, 5, 13, 0, 20, tzinfo=datetime.UTC),
        end=datetime.datetime(2020, 5, 13, 0, 30, tzinfo=datetime.UTC),
    )
    AsyncRaceEntryPause.create(
        entry=entry3,
        start=datetime.datetime(2020, 5, 13, 0, 40, tzinfo=datetime.UTC),
        end=datetime.datetime(2020, 5, 13, 1, 0, tzinfo=datetime.UTC),
    )

    sa = MagicMock(spec=ServerApp)

    # Run
    result = RaceRoomLeaderboard.from_json(room_api.get_leaderboard(sa, room.id, ""))

    # Assert
    assert result == RaceRoomLeaderboard(
        entries=[
            RaceRoomLeaderboardEntry(RandovaniaUser(1235, "The Player"), datetime.timedelta(hours=1)),
            RaceRoomLeaderboardEntry(RandovaniaUser(1236, "Last Player"), datetime.timedelta(hours=1, minutes=30)),
            RaceRoomLeaderboardEntry(
                RandovaniaUser(1234, "The Name"),
                None,
            ),
        ]
    )


def test_get_layout_too_early(simple_room, mocker: pytest_mock.MockFixture):
    # Setup
    now = datetime.datetime(year=2019, month=5, day=12, tzinfo=datetime.UTC)
    mocker.patch("randovania.server.lib.datetime_now", return_value=now)
    mock_verify = mocker.patch("randovania.server.async_race.room_api._verify_authorization")

    sa = MagicMock()
    sa.get_current_user.return_value = User.get_by_id(1234)

    # Run
    with pytest.raises(error.NotAuthorizedForActionError):
        room_api.get_layout(sa, simple_room.id, "AuthTokenx")

    # Assert
    mock_verify.assert_called_once_with(sa, simple_room, "AuthTokenx")


def test_get_layout_valid(simple_room, mocker: pytest_mock.MockFixture):
    # Setup
    now = datetime.datetime(year=2021, month=5, day=12, tzinfo=datetime.UTC)
    mocker.patch("randovania.server.lib.datetime_now", return_value=now)
    mock_verify = mocker.patch("randovania.server.async_race.room_api._verify_authorization")

    sa = MagicMock()
    sa.get_current_user.return_value = User.get_by_id(1234)

    # Run
    result = room_api.get_layout(sa, simple_room.id, "AuthTokenx")

    # Assert
    mock_verify.assert_called_once_with(sa, simple_room, "AuthTokenx")
    assert result == simple_room.layout_description_json


def test_admin_get_admin_data_non_admin(simple_room):
    # Setup
    sa = MagicMock()
    sa.get_current_user.return_value = User.get_by_id(1235)

    # Run
    with pytest.raises(error.NotAuthorizedForActionError):
        room_api.admin_get_admin_data(sa, simple_room.id)


def test_admin_get_admin_data(simple_room):
    # Setup
    sa = MagicMock()
    sa.get_current_user.return_value = User.get_by_id(1234)

    # Run
    result = room_api.admin_get_admin_data(sa, simple_room.id)

    # Assert
    assert result == {
        "users": [
            {
                "user": {"id": 1235, "name": "The Player"},
                "join_date": "2020-05-06T00:00:00+00:00",
                "start_date": "2020-05-11T00:00:00+00:00",
                "finish_date": None,
                "forfeit": False,
                "submission_notes": "",
                "proof_url": "",
                "pauses": [],
            }
        ]
    }


def test_admin_update_entries_admin_only(simple_room):
    # Setup
    sa = MagicMock()
    sa.get_current_user.return_value = User.get_by_id(1235)

    # Run
    with pytest.raises(error.NotAuthorizedForActionError):
        room_api.admin_update_entries(sa, simple_room.id, [])


def test_admin_update_entries(simple_room, mocker: pytest_mock.MockFixture):
    # Setup
    now = datetime.datetime(year=2019, month=5, day=12, tzinfo=datetime.UTC)
    mocker.patch("randovania.server.lib.datetime_now", return_value=now)

    sa = MagicMock()
    sa.get_current_user.return_value = User.get_by_id(1234)

    new_entries = [
        AsyncRaceEntryData(
            user=RandovaniaUser(id=1235, name="ignored"),
            join_date=datetime.datetime(2020, 5, 6, 0, 0, tzinfo=datetime.UTC),
            start_date=datetime.datetime(2020, 6, 6, 0, 0, tzinfo=datetime.UTC),
            finish_date=None,
            forfeit=False,
            pauses=[],
            submission_notes="",
            proof_url="",
        ).as_json
    ]

    # Run
    result = room_api.admin_update_entries(sa, simple_room.id, new_entries)

    # Assert
    assert result == {
        "id": 1,
        "auth_token": ANY,
        "name": "Debug",
        "creator": "The Name",
        "creation_date": "2020-05-02T10:20:00+00:00",
        "start_date": "2020-05-10T00:00:00+00:00",
        "end_date": "2020-06-10T00:00:00+00:00",
        "game_details": ANY,
        "is_admin": True,
        "presets_raw": [ANY],
        "race_status": "scheduled",
        "self_status": "not-member",
        "visibility": "visible",
        "allow_pause": True,
    }
    assert [x.as_entry() for x in simple_room.audit_log] == [
        AuditEntry(user="The Name", message="Modified entries for ['ignored'].", time=ANY)
    ]


def test_join_and_export_too_early(simple_room, mocker: pytest_mock.MockFixture):
    # Setup
    now = datetime.datetime(year=2019, month=5, day=12, tzinfo=datetime.UTC)
    mocker.patch("randovania.server.lib.datetime_now", return_value=now)
    mock_verify = mocker.patch("randovania.server.async_race.room_api._verify_authorization")

    sa = MagicMock()
    sa.get_current_user.return_value = User.get_by_id(1234)

    with pytest.raises(error.NotAuthorizedForActionError):
        room_api.join_and_export(sa, simple_room.id, "AuthTokenz", {})

    mock_verify.assert_called_once_with(sa, simple_room, "AuthTokenz")


def test_join_and_export_success(simple_room, mocker: pytest_mock.MockFixture):
    # Setup
    now = datetime.datetime(year=2020, month=5, day=12, tzinfo=datetime.UTC)
    mocker.patch("randovania.server.lib.datetime_now", return_value=now)
    mock_data = mocker.patch("randovania.games.prime2.exporter.patch_data_factory.EchoesPatchDataFactory.create_data")
    mock_verify = mocker.patch("randovania.server.async_race.room_api._verify_authorization")

    sa = MagicMock()
    sa.get_current_user.return_value = User.get_by_id(1234)

    # Run
    result = room_api.join_and_export(sa, simple_room.id, "AuthTokenz", {})

    # Assert
    mock_verify.assert_called_once_with(sa, simple_room, "AuthTokenz")
    assert result is mock_data.return_value


def test_get_own_proof(simple_room):
    # Setup
    sa = MagicMock()
    sa.get_current_user.return_value = User.get_by_id(1235)

    entry = AsyncRaceEntry.entry_for(simple_room, sa.get_current_user.return_value)
    entry.finish_datetime = datetime.datetime(year=2020, month=5, day=12, tzinfo=datetime.UTC)
    entry.save()

    # Run
    notes, url = room_api.get_own_proof(sa, simple_room.id)

    # Assert
    assert notes == ""
    assert url == ""


def test_submit_proof_not_joined(simple_room):
    # Setup
    sa = MagicMock()
    sa.get_current_user.return_value = User.get_by_id(1234)

    # Run
    with pytest.raises(error.NotAuthorizedForActionError):
        room_api.submit_proof(sa, simple_room.id, "notes", "")


def test_submit_proof_not_finished(simple_room):
    # Setup
    sa = MagicMock()
    sa.get_current_user.return_value = User.get_by_id(1235)

    # Run
    with pytest.raises(error.InvalidActionError, match="Only possible to submit proof after finishing"):
        room_api.submit_proof(sa, simple_room.id, "notes", "")


def test_submit_proof_valid(simple_room):
    # Setup
    sa = MagicMock()
    sa.get_current_user.return_value = User.get_by_id(1235)

    entry = AsyncRaceEntry.entry_for(simple_room, sa.get_current_user.return_value)
    entry.finish_datetime = datetime.datetime(year=2020, month=5, day=12, tzinfo=datetime.UTC)
    entry.save()

    # Run
    room_api.submit_proof(sa, simple_room.id, "notes", "")

    # Assert
    entry = AsyncRaceEntry.entry_for(simple_room, sa.get_current_user.return_value)
    assert entry.submission_notes == "notes"
    assert entry.proof_url == ""

    assert [x.as_entry() for x in simple_room.audit_log] == [
        AuditEntry(user="The Player", message="Updated submission notes and proof.", time=ANY)
    ]


def test_get_audit_log(simple_room, mocker: pytest_mock.MockFixture):
    # Setup
    sa = MagicMock()
    sa.get_current_user.return_value = User.get_by_id(1235)
    mock_verify = mocker.patch("randovania.server.async_race.room_api._verify_authorization")

    AsyncRaceAuditEntry.create(
        room=simple_room,
        user=User.get_by_id(1235),
        message="Someone did a thing",
        time=datetime.datetime(year=2020, month=5, day=12, tzinfo=datetime.UTC),
    )

    # Run
    result = room_api.get_audit_log(sa, simple_room.id, "AuthTokenx")

    # Assert
    mock_verify.assert_called_once_with(sa, simple_room, "AuthTokenx")
    assert result == [
        {"user": "The Player", "message": "Someone did a thing", "time": "2020-05-12T00:00:00+00:00"},
    ]
