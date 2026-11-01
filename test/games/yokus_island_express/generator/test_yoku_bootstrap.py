from __future__ import annotations

import dataclasses

import pytest

from randovania.game.game_enum import RandovaniaGame
from randovania.game_description import default_database
from randovania.game_description.resources.resource_type import ResourceType
from randovania.games.yokus_island_express.generator.bootstrap import YokuBootstrap
from randovania.games.yokus_island_express.layout.yokus_island_express_configuration import BEACON_COUNT


@pytest.mark.parametrize("required_beacons", range(BEACON_COUNT + 1))
def test_enabled_misc_resources(preset_manager, required_beacons: int) -> None:
    game = default_database.game_description_for(RandovaniaGame.YOKUS_ISLAND_EXPRESS)
    preset = preset_manager.default_preset_for_game(RandovaniaGame.YOKUS_ISLAND_EXPRESS).get_preset()
    configuration = dataclasses.replace(preset.configuration, required_beacons=required_beacons)
    resource_database = game.get_resource_database_view()

    enabled = dict(YokuBootstrap().misc_resources_for_configuration(configuration, resource_database))

    assert {resource.short_name for resource, amount in enabled.items() if amount > 0} == {
        f"RequiredBeacons{required_beacons}"
    }
    assert {f"RequiredBeacons{n}" for n in range(BEACON_COUNT + 1)} <= {
        resource.short_name for resource in resource_database.get_all_resources_of_type(ResourceType.MISC)
    }
