import dataclasses

from randovania.generator.item_pool import pool_creator
from randovania.layout.prime2.echoes_configuration import LayoutSkyTempleKeyMode


def test_calculate_pool_item_count(default_layout_configuration):
    layout_configuration = dataclasses.replace(
        default_layout_configuration,
        major_items_configuration=dataclasses.replace(
            default_layout_configuration.major_items_configuration,
            minimum_random_starting_items=2,
        ),
        sky_temple_keys=LayoutSkyTempleKeyMode.ALL_BOSSES,
    )

    # Run
    result = pool_creator.calculate_pool_item_count(layout_configuration)

    # Assert
    assert result == (118, 121)
