import datetime
from unittest.mock import MagicMock

from randovania.network_common.async_race_room import (
    AsyncRaceRoomUserStatus,
    RaceRoomLeaderboard,
    RaceRoomLeaderboardEntry,
)
from randovania.network_common.user import RandovaniaUser
from randovania.server.async_race import room_api
from randovania.server.database import AsyncRaceEntry, AsyncRaceEntryPause, AsyncRaceRoom, User
from randovania.server.server_app import ServerApp


def test_finish(simple_room):
    room = AsyncRaceRoom.get_by_id(1)
    user = User.get_by_id(1235)
    entry = AsyncRaceEntry.entry_for(room, user)

    sa = MagicMock(spec=ServerApp)
    sa.get_current_user.return_value = user

    assert entry.user_status() == AsyncRaceRoomUserStatus.STARTED
    room_api.change_state(sa, room.id, AsyncRaceRoomUserStatus.FINISHED.value)
    assert AsyncRaceEntry.entry_for(room, user).user_status() == AsyncRaceRoomUserStatus.FINISHED


def test_get_leaderboard(simple_room):
    # Setup
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
    result = RaceRoomLeaderboard.from_json(room_api.get_leaderboard(sa, room.id))

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
