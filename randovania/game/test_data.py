from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Collection, Container

    from randovania.layout.base.trick_level import LayoutTrickLevel


@dataclasses.dataclass(frozen=True, kw_only=True)
class GameTestData:
    """Contains data and configuration parameters to allow the test suit to assert things properly for this game."""

    expected_seed_hash: bytes
    """The seed hash expected for the layout generated in test_create_description."""

    generator_test_seed_number: int = 0
    """The seed number used in test_create_description."""

    database_collectable_ignore_events: Container[str] = dataclasses.field(default_factory=tuple)
    """For test_database_collectable, the list of Events that are expected to not be collected."""

    database_collectable_ignore_pickups: Container[int] = dataclasses.field(default_factory=tuple)
    """For test_database_collectable, the list of Pickup Indices that are expected to not be collected."""

    database_collectable_include_tricks: Collection[tuple[str, LayoutTrickLevel]] = dataclasses.field(
        default_factory=tuple
    )
    """For test_database_collectable, the list of tricks and their respective levels to use when running the reach."""
