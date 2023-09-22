from __future__ import annotations

from enum import Enum

from randovania.lib import enum_lib


class GameConnectionStatus(Enum):
    pretty_text: str

    Disconnected = "disconnected"
    TitleScreen = "title-screen"
    InGame = "in-game"


enum_lib.add_per_enum_field(
    GameConnectionStatus,
    "pretty_text",
    {
        GameConnectionStatus.Disconnected: "Disconnected",
        GameConnectionStatus.TitleScreen: "Title screen",
        GameConnectionStatus.InGame: "In-game",
    },
)
