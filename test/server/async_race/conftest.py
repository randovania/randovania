from __future__ import annotations

import datetime
import json

import pytest

from randovania.layout.layout_description import LayoutDescription
from randovania.network_common.game_details import GameDetails
from randovania.network_common.session_visibility import MultiplayerSessionVisibility
from randovania.server import database


@pytest.fixture
def simple_room(clean_database, test_files_dir) -> database.AsyncRaceRoom:
    description = LayoutDescription.from_file(test_files_dir.joinpath("log_files", "prime2_seed_b.rdvgame"))

    user1 = database.User.create(id=1234, name="The Name")
    user2 = database.User.create(id=1235, name="The Player")

    room = database.AsyncRaceRoom.create(
        id=1,
        name="Debug",
        state=MultiplayerSessionVisibility.VISIBLE,
        layout_description_json=description.as_binary(),
        game_details_json=json.dumps(
            GameDetails(
                seed_hash="seed_hash",
                word_hash="word_hash",
                spoiler=True,
            ).as_json
        ),
        creator=user1,
        creation_date=datetime.datetime(2020, 5, 2, 10, 20, tzinfo=datetime.UTC),
        start_date=datetime.datetime(2020, 5, 10, 0, 0, tzinfo=datetime.UTC),
        end_date=datetime.datetime(2020, 6, 10, 0, 0, tzinfo=datetime.UTC),
        allow_pause=True,
    )
    room.save()

    database.AsyncRaceEntry.create(
        room=room,
        user=user2,
        join_date=datetime.datetime(2020, 5, 6, 0, 0, tzinfo=datetime.UTC),
        start_date=datetime.datetime(2020, 5, 11, 0, 0, tzinfo=datetime.UTC),
    )

    return room
