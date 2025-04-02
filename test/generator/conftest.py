from __future__ import annotations

import pytest

from randovania.generator.filler.filler_configuration import FillerConfiguration
from randovania.layout.base.available_locations import RandomizationMode
from randovania.layout.base.logical_resource_action import LayoutLogicalResourceAction


@pytest.fixture
def default_filler_config() -> FillerConfiguration:
    return FillerConfiguration(
        randomization_mode=RandomizationMode.FULL,
        minimum_random_starting_pickups=0,
        maximum_random_starting_pickups=0,
        indices_to_exclude=frozenset(),
        logical_resource_action=LayoutLogicalResourceAction.RANDOMLY,
        first_progression_must_be_local=False,
        minimum_available_locations_for_hint_placement=0,
        minimum_location_weight_for_hint_placement=0,
        single_set_for_pickups_that_solve=False,
        staggered_multi_pickup_placement=False,
        fallback_to_reweight_with_unsafe=False,
        consider_possible_unsafe_resources=False,
    )
