from unittest.mock import MagicMock

from randovania.network_common.async_race_room import AsyncRaceRoomUserStatus
from randovania.server.async_race import room_api
from randovania.server.database import AsyncRaceEntry, AsyncRaceRoom, User
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
