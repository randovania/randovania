from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING, Any, Self

from PySide6 import QtCore, QtWidgets

if TYPE_CHECKING:
    from randovania.game_description.db.area import Area
    from randovania.game_description.db.region import Region
    from randovania.game_description.game_description import GameDescription
    from randovania.generator.pickup_pool import PoolResults
    from randovania.graph.state import State
    from randovania.graph.world_graph import WorldGraph
    from randovania.gui.tracker.tracker_state import TrackerState
    from randovania.layout.base.base_configuration import BaseConfiguration
    from randovania.resolver.logic import Logic


@dataclasses.dataclass(frozen=True)
class TrackerComponentSetup:
    """Everything a TrackerComponent needs to decide if it applies to a game, and to create itself."""

    game_description: GameDescription
    graph: WorldGraph
    logic: Logic
    configuration: BaseConfiguration
    pickup_pool: PoolResults


class TrackerComponent(QtWidgets.QDockWidget):
    """
    A dockable part of the TrackerWindow, responsible for one aspect of the tracked state.

    Components never talk to each other: they report changes to the window via the signals below, and the window
    broadcasts the resulting TrackerState back to everyone via `tracker_update`.
    """

    # Which area of the window this component is docked into by default.
    dock_area = QtCore.Qt.DockWidgetArea.RightDockWidgetArea

    StateChanged = QtCore.Signal()
    """The user changed something here that invalidates the current tracker state."""

    ActionRequested = QtCore.Signal(object)
    """The user asked for the given WorldGraphNode to be added to the action list."""

    @classmethod
    def create_for(cls, setup: TrackerComponentSetup) -> Self | None:
        """Creates this component, or None if it's not applicable to the game being tracked."""
        raise NotImplementedError

    def reset(self) -> None:
        """Returns this component to how it was when the tracker was first opened."""

    def decode_persisted_state(self, previous_state: dict) -> Any | None:
        """
        Reads this component's data out of a persisted state, without applying it.
        Returning None aborts restoring the entire tracker, so a component that persists nothing returns any
        other value.
        """
        return True

    def apply_previous_state(self, previous_state: Any) -> None:
        """Applies a value previously returned by `decode_persisted_state`."""

    def persist_current_state(self) -> dict:
        """The fields this component contributes to the persisted state file."""
        return {}

    def update_graph(self) -> None:
        """Applies this component's configuration to the WorldGraph, before a new State is calculated."""

    def fill_into_state(self, state: State) -> None:
        """Applies this component's configuration to a freshly created State."""

    def tracker_update(self, tracker_state: TrackerState) -> None:
        """The tracker state changed, refresh whatever this component displays."""

    def focus_on_region(self, region: Region) -> None:
        """Asks this component to display the given region, if it displays regions at all."""

    def focus_on_area(self, area: Area) -> None:
        """Asks this component to display the given area, if it displays areas at all."""
