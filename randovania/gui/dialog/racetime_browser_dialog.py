import dataclasses
import datetime

import aiohttp
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton, QDialogButtonBox, QDialog, QTableWidgetItem, QCheckBox
from qasync import asyncSlot

from randovania.games.game import RandovaniaGame
from randovania.gui.generated.racetime_browser_dialog_ui import Ui_RacetimeBrowserDialog
from randovania.gui.lib import common_qt_lib, async_dialog
from randovania.gui.lib.qt_network_client import handle_network_errors
from randovania.layout.permalink import Permalink, UnsupportedPermalink


@dataclasses.dataclass(frozen=True)
class RaceEntry:
    name: str
    status: str
    verbose_status: str
    entrants: int
    goal: str
    opened_at: datetime.datetime
    info: str
    game: RandovaniaGame

    @classmethod
    def from_json(cls, data, game) -> "RaceEntry":
        return RaceEntry(
            name=data["name"],
            status=data["status"]["value"],
            verbose_status=data["status"]["verbose_value"],
            entrants=data["entrants_count"],
            goal=data["goal"]["name"],
            opened_at=datetime.datetime.fromisoformat(data["opened_at"].replace("Z", "+00:00")),
            info=data["info"],
            game=game,
        )


_SUPPORTED_GAME_URLS = {
    RandovaniaGame.METROID_PRIME: "https://racetime.gg/mpr/data",
    RandovaniaGame.METROID_PRIME_ECHOES: "https://racetime.gg/mp2r/data",
}
_TEST_RESPONSE = {
    "name": "Metroid Prime 2: Echoes Randomizer",
    "short_name": "MP2R",
    "slug": "mp2r",
    "url": "/mp2r",
    "data_url": "/mp2r/data",
    "image": None,
    "info": "Download the Metroid Prime 2: Echoes randomizer <a href=\"https://github.com/randovania/randovania/releases\">here</a>.\r\n<p><p>\r\n<b><u>Category Rules</b></u>\r\n<p><p>\r\nTiming starts when confirming the game's difficulty on the main menu (or selecting a new file, if you are not able to select a difficulty). \r\n<p><p>\r\n<b>Beat the game</b>: Timing stops once you have activated a cutscene, elevator, portal, or teleport that will lead to the credits or Mission Final screen without any further game input.\r\n <p>\r\n<b>Collect all Sky Temple Keys</b>: Timing stops once you have at least one of each available Sky Temple Key (Sky Temple Key 1, 2, 3, etc.) currently collected. \r\n<p>\r\n<b><u>Miscellaneous</b></u>\r\n<p><p>\r\nThe only permitted emulator is Dolphin, running on version 5.0 or later. Running the ISO on console via Nintendont is allowed.\r\n<p>\r\nISO inspection/ROM inspection/memory inspection/software reverse-engineering that determines item locations or elevator destinations of the race seed prior to or during the race is <b>banned</b>.\r\n<p>\r\nTurbo functions, increasing the disk read speed, save states, fast forward and disabling fog are all <b>banned</b>. However, any of these functions may be allowed if all racers permit it, or a category rule permits it.",
    "streaming_required": False,
    "owners": [
        {
            "id": "q5rNGD3DYAo9blOy",
            "full_name": "gollop#9668",
            "name": "gollop",
            "discriminator": "9668",
            "url": "/user/q5rNGD3DYAo9blOy",
            "avatar": None,
            "pronouns": "they/them",
            "flair": "moderator",
            "twitch_name": "golloppp",
            "twitch_display_name": "golloppp",
            "twitch_channel": "https://www.twitch.tv/golloppp",
            "can_moderate": True
        }
    ],
    "moderators": [],
    "current_races": [
        {
            "name": "mp2r/proud-stadium-7340",
            "status": {
                "value": "in_progress",
                "verbose_value": "In progress",
                "help_text": "Race is in progress"
            },
            "url": "/mp2r/proud-stadium-7340",
            "data_url": "/mp2r/proud-stadium-7340/data",
            "goal": {
                "name": "Beat the game",
                "custom": False
            },
            "info": "zasj0oGRVOUaUwbx6LFMgLrjmF0kH2aEFX9OMr1tu7xcW8az || Seed Hash: Command Caretaker Alcove (67J3ZJPT)",
            "entrants_count": 3,
            "entrants_count_inactive": 0,
            "opened_at": "2020-10-03T18:44:17.865Z",
            "started_at": "2020-10-03T18:45:17.865Z",
            "time_limit": "P1DT00H00M00S"
        },
        {
            "name": "mp2r/proud-arena-4584",
            "status": {
                "value": "open",
                "verbose_value": "Open",
                "help_text": "Anyone may join this race"
            },
            "url": "/mp2r/proud-arena-4584",
            "data_url": "/mp2r/proud-arena-4584/data",
            "goal": {
                "name": "Beat the game",
                "custom": False
            },
            "info": "yevhOB287u6SOly2HFReAapCZprQOvB9fVaU5-EAvS08qoQi  || Seed Hash: Sandigger Module Boom (GN73RSFH)",
            "entrants_count": 5,
            "entrants_count_inactive": 0,
            "opened_at": "2020-10-03T18:46:17.865Z",
            "started_at": None,
            "time_limit": "P1DT00H00M00S"
        }
    ]
}


async def _query_server(race_url) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(race_url) as response:
            response.raise_for_status()
            return await response.json()


class RacetimeBrowserDialog(QDialog, Ui_RacetimeBrowserDialog):
    races: list[RaceEntry]
    permalink: Permalink | None = None

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        common_qt_lib.set_default_window_icon(self)

        self.refresh_button = QPushButton("Refresh")
        self.button_box.addButton(self.refresh_button, QDialogButtonBox.ResetRole)
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
        self.button_box.button(QDialogButtonBox.Ok).setText("Import")

        self.button_box.accepted.connect(self.attempt_join)
        self.button_box.rejected.connect(self.reject)
        self.refresh_button.clicked.connect(self.refresh)

        self._status_checks = (
            (self.status_open_check, "open"),
            (self.status_invitational_check, "invitational"),
            (self.status_pending_check, "pending"),
            (self.status_inprogress_check, "in_progress"),
            (self.status_finished_check, "finished"),
            (self.status_cancelled_check, "cancelled"),
        )
        for check, _ in self._status_checks:
            check.stateChanged.connect(self.update_list)
        self.filter_name_edit.textEdited.connect(self.update_list)

        self._game_checks = set()
        for game in _SUPPORTED_GAME_URLS:
            game_checkbox = QCheckBox(game.long_name)
            game_checkbox.setChecked(True)
            self.game_check_layout.addWidget(game_checkbox)
            game_checkbox.stateChanged.connect(self.update_list)
            self._game_checks.add((game_checkbox, game))

        self.table_widget.itemSelectionChanged.connect(self.on_selection_changed)
        self.table_widget.itemDoubleClicked.connect(self.on_double_click)

    @asyncSlot()
    @handle_network_errors
    async def refresh(self) -> bool:
        self.refresh_button.setEnabled(False)
        self.races = []
        try:
            for game in _SUPPORTED_GAME_URLS:
                race_url = _SUPPORTED_GAME_URLS[game]
                try:
                    raw_races = await _query_server(race_url)
                except aiohttp.ClientError as e:
                    await async_dialog.warning(self, "Connection error",
                                               f"Unable to retrieve races from `{race_url}`: {e}")
                    return False

                self.races.extend([RaceEntry.from_json(item, game) for item in raw_races["current_races"]])
            self.update_list()
            return True
        finally:
            self.refresh_button.setEnabled(True)

    def on_selection_changed(self):
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(len(self.table_widget.selectedItems()) > 0)

    @property
    def selected_race(self):
        return self.table_widget.selectedItems()[0].data(Qt.UserRole)

    @asyncSlot(QTableWidgetItem)
    async def on_double_click(self, item: QTableWidgetItem):
        await self.attempt_join()

    @asyncSlot()
    @handle_network_errors
    async def attempt_join(self):
        if not self.races:
            return

        race = self.selected_race

        permalink = None

        for word in race.info.split(" "):
            try:
                permalink = Permalink.from_str(word)
            except ValueError:
                continue
            except UnsupportedPermalink:
                continue

        if permalink is None:
            await async_dialog.warning(self, "Missing permalink",
                                       "Unable to get a valid Permalink from this race's info.")
        else:
            self.permalink = permalink
            return self.accept()

    def update_list(self):
        self.table_widget.clear()
        self.table_widget.setHorizontalHeaderLabels(["Name", "Game", "Status", "Entrants",
                                                     "Goal", "Info", "Opened At"])

        name_filter = self.filter_name_edit.text().strip()

        displayed_status = set()
        for (check, status) in self._status_checks:
            if check.isChecked():
                displayed_status.add(status)

        displayed_games = set()
        for (check, game) in self._game_checks:
            if check.isChecked():
                displayed_games.add(game)

        visible_races = [
            race
            for race in self.races
            if (race.status in displayed_status
                and name_filter in race.name
                and race.game in displayed_games)
        ]

        self.table_widget.setRowCount(len(visible_races))
        for i, session in enumerate(visible_races):
            name = QTableWidgetItem(session.name)
            status = QTableWidgetItem(session.verbose_status)
            entrants = QTableWidgetItem(str(session.entrants))
            goal = QTableWidgetItem(session.goal)
            info = QTableWidgetItem(session.info)
            opened_at = QTableWidgetItem(session.opened_at.astimezone().strftime("%c"))
            game_name = QTableWidgetItem(session.game.short_name)

            name.setData(Qt.UserRole, session)
            self.table_widget.setItem(i, 0, name)
            self.table_widget.setItem(i, 1, game_name)
            self.table_widget.setItem(i, 2, status)
            self.table_widget.setItem(i, 3, entrants)
            self.table_widget.setItem(i, 4, goal)
            self.table_widget.setItem(i, 5, info)
            self.table_widget.setItem(i, 6, opened_at)

        self.status_label.setText(f"{len(self.races)} races total, {len(visible_races)} displayed.")
