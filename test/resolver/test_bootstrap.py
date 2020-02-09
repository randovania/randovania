import pytest

from randovania.game_description.resources.resource_type import ResourceType
from randovania.layout.layout_configuration import LayoutElevators
from randovania.layout.translator_configuration import TranslatorConfiguration
from randovania.resolver import bootstrap


@pytest.mark.parametrize("elevators", [LayoutElevators.VANILLA, LayoutElevators.TWO_WAY_RANDOMIZED])
def test_create_vanilla_translator_resources(echoes_resource_database,
                                             elevators: LayoutElevators,
                                             ):
    # Setup
    gfmc_resource = echoes_resource_database.get_by_type_and_index(ResourceType.TRICK, 16)
    torvus_resource = echoes_resource_database.get_by_type_and_index(ResourceType.TRICK, 17)
    great_resource = echoes_resource_database.get_by_type_and_index(ResourceType.TRICK, 18)

    # Run
    result = bootstrap._create_vanilla_translator_resources(echoes_resource_database, elevators)

    # Assert
    assert result == {
        gfmc_resource: 0,
        torvus_resource: 0,
        great_resource: 0 if elevators != LayoutElevators.VANILLA else 1,
    }
