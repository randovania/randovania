from unittest.mock import MagicMock

from randovania.games.prime import binary_data
from randovania.resolver import data_reader, generator
from randovania.resolver.layout_configuration import LayoutConfiguration, LayoutLogic, LayoutMode, LayoutRandomizedFlag, \
    LayoutEnabledFlag, LayoutDifficulty
from randovania.resolver.layout_description import LayoutDescription


def test_generate_list():
    status_update = MagicMock()
    game = data_reader.decode_data(binary_data.decode_default_prime2(), [])

    configuration = LayoutConfiguration(seed_number=1027649936, logic=LayoutLogic.NO_GLITCHES, mode=LayoutMode.STANDARD,
                                        sky_temple_keys=LayoutRandomizedFlag.RANDOMIZED,
                                        item_loss=LayoutEnabledFlag.ENABLED, elevators=LayoutRandomizedFlag.VANILLA,
                                        hundo_guaranteed=LayoutEnabledFlag.DISABLED, difficulty=LayoutDifficulty.NORMAL)

    description = LayoutDescription(
        configuration=configuration,
        version='0.9.1',
        pickup_mapping=(24, None, None, None, 38, 102, None, None, None, 57, 118, 15, 91, 113, None, None,
                        52, 74, 115, None, 53, 23, None, 82, None, None, 79, None, None, None, 75, None,
                        50, 39, 11, 106, None, None, 88, 117, 112, None, 44, None, 46, None, 68, None,
                        None, None, 1, None, None, None, 86, 37, None, 19, None, None, None, None, None,
                        None, None, None, None, None, None, None, None, None, None, 45, None, None, None,
                        None, None, None, None, None, None, None, None, None, None, None, None, None,
                        None, None, None, None, None, None, None, None, None, None, None, None, None,
                        None, None, None, None, None, None, None, None, None, None, None, None, None,
                        None, None, None),
        solver_path=())

    generated_description = generator.generate_list(game, configuration, status_update=status_update)

    assert LayoutDescription(
        configuration=generated_description.configuration,
        version=generated_description.version,
        pickup_mapping=generated_description.pickup_mapping,
        solver_path=()) == description
