from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from PySide6 import QtWidgets

from randovania.gui.dialog.async_race_admin_dialog import AsyncRaceAdminDialog
from randovania.network_common.async_race_room import AsyncRaceEntryData, AsyncRaceRoomAdminData
from randovania.network_common.user import RandovaniaUser

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot


def test_admin_data(skip_qtbot: QtBot):
    parent = QtWidgets.QMainWindow()
    skip_qtbot.add_widget(parent)

    admin_data = AsyncRaceRoomAdminData(
        [
            AsyncRaceEntryData(
                user=RandovaniaUser(id=1235, name="user"),
                join_date=datetime.datetime(2020, 5, 6, 0, 0, tzinfo=datetime.UTC),
                start_date=datetime.datetime(2020, 6, 6, 0, 0, tzinfo=datetime.UTC),
                finish_date=datetime.datetime(2020, 7, 7, 0, 0, tzinfo=datetime.UTC),
                forfeit=False,
                pauses=[],
                submission_notes="notes",
                proof_url="url",
            )
        ]
    )
    dialog = AsyncRaceAdminDialog(parent, admin_data)

    # Assert
    assert dialog.admin_data() == admin_data
