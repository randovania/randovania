import pytest

from randovania.game_description.resources.resource_type import ResourceType
from randovania.layout.translator_configuration import TranslatorConfiguration
from randovania.resolver import bootstrap


@pytest.mark.parametrize("fixed_gfmc_compound", [False, True])
@pytest.mark.parametrize("fixed_torvus_temple", [False, True])
@pytest.mark.parametrize("fixed_great_temple", [False, True])
def test_create_vanilla_translator_resources(echoes_resource_database,
                                             fixed_gfmc_compound: bool,
                                             fixed_torvus_temple: bool,
                                             fixed_great_temple: bool,
                                             ):
    # Setup
    translator_configuration = TranslatorConfiguration(
        {},
        fixed_gfmc_compound=fixed_gfmc_compound,
        fixed_torvus_temple=fixed_torvus_temple,
        fixed_great_temple=fixed_great_temple,
    )
    gfmc_resource = echoes_resource_database.get_by_type_and_index(ResourceType.TRICK, 16)
    torvus_resource = echoes_resource_database.get_by_type_and_index(ResourceType.TRICK, 17)
    great_resource = echoes_resource_database.get_by_type_and_index(ResourceType.TRICK, 18)

    # Run
    result = bootstrap._create_vanilla_translator_resources(echoes_resource_database, translator_configuration)

    # Assert
    assert result == {
        gfmc_resource: 0 if fixed_gfmc_compound else 1,
        torvus_resource: 0 if fixed_torvus_temple else 1,
        great_resource: 0 if fixed_great_temple else 1,
    }
