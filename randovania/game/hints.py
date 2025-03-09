from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from randovania.generator.hint_distributor import HintDistributor


@dataclasses.dataclass(frozen=True)
class SpecificHintDetails:
    long_name: str
    description: str

    disabled_details: str = "Provides no useful information."
    hide_area_details: str = "Indicates only which region the pickup is in."
    precise_details: str = "Indicates the exact region and area the pickup is in."

    show_in_gui: bool = True


@dataclasses.dataclass(frozen=True)
class GameHints:
    hint_distributor: HintDistributor
    """Use AllJokesDistributor if not using hints."""

    specific_pickup_hints: dict[str, SpecificHintDetails]
    """
    Defines each category of specific pickup hint this game uses,
    as well as how they should appear in the preset tab.
    """
