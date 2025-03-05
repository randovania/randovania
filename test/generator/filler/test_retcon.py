from __future__ import annotations

from unittest.mock import MagicMock

from randovania.generator.filler.retcon import should_be_starting_pickup
from randovania.layout.base.standard_pickup_state import StartingItemBehavior


def test_invalid_starting_items():
    pickup_entry = MagicMock()
    pickup_entry.start_case = StartingItemBehavior.CAN_NEVER_BE_STARTING

    assert not should_be_starting_pickup(MagicMock(), MagicMock(), pickup_entry)
