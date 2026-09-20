from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

import pytest
from PySide6 import QtCore, QtWidgets

if TYPE_CHECKING:
    from collections.abc import Iterator

from randovania.gui.widgets.async_race_room_settings_widget import AsyncRaceRoomSettingsWidget
from randovania.network_common.async_race_room import AsyncRaceSettings
from randovania.network_common.session_visibility import MultiplayerSessionVisibility


@pytest.fixture
def widget(skip_qtbot) -> Iterator[AsyncRaceRoomSettingsWidget]:
    parent = QtWidgets.QWidget()
    skip_qtbot.addWidget(parent)

    result = AsyncRaceRoomSettingsWidget(parent)
    result.ui.name_edit.setText("The Room")

    # qtbot only keeps a weakref, so `parent` has to stay referenced for the duration of the test.
    # If it gets collected, Qt destroys the whole widget tree with it. Hence yield over return.
    yield result  # noqa: PT022


def test_create_settings_object_uses_utc(widget: AsyncRaceRoomSettingsWidget):
    """
    The time edits show the user's local time, but the server is only ever given aware UTC datetimes.
    Asserted via the timestamp, so this holds no matter what timezone the tests run in.
    """
    start = QtCore.QDateTime(2020, 1, 1, 12, 0, 0)
    end = QtCore.QDateTime(2020, 1, 2, 18, 30, 0)
    widget.ui.start_time_edit.setDateTime(start)
    widget.ui.end_time_edit.setDateTime(end)

    # Run
    settings = widget.create_settings_object()

    # Assert
    assert settings.start_date.tzinfo is datetime.UTC
    assert settings.end_date.tzinfo is datetime.UTC
    assert settings.start_date.timestamp() == start.toSecsSinceEpoch()
    assert settings.end_date.timestamp() == end.toSecsSinceEpoch()


def test_create_settings_object_round_trips_through_json(widget: AsyncRaceRoomSettingsWidget):
    """What `as_json` sends to the server must describe the same instant the user picked."""
    start = QtCore.QDateTime(2020, 1, 1, 12, 0, 0)
    widget.ui.start_time_edit.setDateTime(start)

    # Run
    settings = widget.create_settings_object()
    decoded = AsyncRaceSettings.from_json(settings.as_json)

    # Assert
    assert decoded == settings
    assert decoded.start_date.timestamp() == start.toSecsSinceEpoch()


def test_naive_datetimes_are_rejected():
    """A naive datetime would be silently off by the user's UTC offset, so it must not be accepted."""
    with pytest.raises(ValueError, match="should have timezone info"):
        AsyncRaceSettings(
            name="The Room",
            password=None,
            start_date=datetime.datetime(2020, 1, 1),
            end_date=datetime.datetime(2020, 1, 2, tzinfo=datetime.UTC),
            visibility=MultiplayerSessionVisibility.VISIBLE,
            allow_pause=False,
        )
