from unittest.mock import MagicMock

import pytest

from randovania.game_description.resources.resource_type import ResourceType
from randovania.layout.teleporters import TeleporterShuffleMode
from randovania.resolver import bootstrap


@pytest.mark.parametrize("vanilla_elevators", [False, True])
def test_misc_resources_for_configuration(echoes_resource_database,
                                          vanilla_elevators: bool,
                                          ):
    # Setup
    configuration = MagicMock()
    configuration.elevators.is_vanilla = vanilla_elevators
    gfmc_resource = echoes_resource_database.get_by_type_and_index(ResourceType.MISC, 16)
    torvus_resource = echoes_resource_database.get_by_type_and_index(ResourceType.MISC, 17)
    great_resource = echoes_resource_database.get_by_type_and_index(ResourceType.MISC, 18)

    # Run
    result = bootstrap.misc_resources_for_configuration(configuration, echoes_resource_database)
    relevant_tricks = {
        trick: result[trick]
        for trick in [gfmc_resource, torvus_resource, great_resource]
    }

    # Assert
    assert relevant_tricks == {
        gfmc_resource: 0,
        torvus_resource: 0,
        great_resource: 0 if not vanilla_elevators else 1,
    }


def test_logic_bootstrap(default_preset, echoes_game_description):
    new_game, state = bootstrap.logic_bootstrap(default_preset.configuration, echoes_game_description,
                                                echoes_game_description.create_game_patches())

    
