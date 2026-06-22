from __future__ import annotations

from typing import TYPE_CHECKING, override

from randovania.game_description.db.dock import DockType
from randovania.gui.game_details.dock_weakness_distribution_details_tab import DockWeaknessDistributionDetailsTab

if TYPE_CHECKING:
    from randovania.game_description.game_database_view import GameDatabaseView


class DoorLockRandoDetailsTab(DockWeaknessDistributionDetailsTab):
    """A special case for Dock Weakness Distribution, when dealing with Doors."""

    @override
    def tab_title(self) -> str:
        return "Door Locks"

    @classmethod
    @override
    def dock_type(cls, game: GameDatabaseView) -> DockType:
        return game.find_dock_type_by_short_name("door")
