from unittest.mock import MagicMock

from randovania.games.prime import binary_data
from randovania.resolver import data_reader, generator, debug
from randovania.resolver.layout_configuration import LayoutConfiguration, LayoutLogic, LayoutMode, LayoutRandomizedFlag, \
    LayoutEnabledFlag, LayoutDifficulty
from randovania.resolver.layout_description import LayoutDescription


def _run_generation_comparison(
        configuration: LayoutConfiguration,
        pickup_mapping,
):
    debug._DEBUG_LEVEL = 1
    status_update = MagicMock()
    game = data_reader.decode_data(binary_data.decode_default_prime2(), [])

    description = LayoutDescription(
        configuration=configuration,
        version='0.9.1',
        pickup_mapping=pickup_mapping,
        solver_path=())

    generated_description = generator.generate_list(game, configuration, status_update=status_update)

    assert LayoutDescription(
        configuration=generated_description.configuration,
        version=generated_description.version,
        pickup_mapping=generated_description.pickup_mapping,
        solver_path=()) == description


def test_generate_list():
    _run_generation_comparison(
        configuration=LayoutConfiguration(seed_number=1027649936, logic=LayoutLogic.NO_GLITCHES,
                                          mode=LayoutMode.STANDARD,
                                          sky_temple_keys=LayoutRandomizedFlag.RANDOMIZED,
                                          item_loss=LayoutEnabledFlag.ENABLED, elevators=LayoutRandomizedFlag.VANILLA,
                                          hundo_guaranteed=LayoutEnabledFlag.DISABLED,
                                          difficulty=LayoutDifficulty.NORMAL),
        pickup_mapping=(24, None, None, None, 38, 102, None, None, None, 57, 118, 15, 91, 113, None, None,
                        52, 74, 115, None, 53, 23, None, 82, None, None, 79, None, None, None, 75, None,
                        50, 39, 11, 106, None, None, 88, 117, 112, None, 44, None, 46, None, 68, None,
                        None, None, 1, None, None, None, 86, 37, None, 19, None, None, None, None, None,
                        None, None, None, None, None, None, None, None, None, None, 45, None, None, None,
                        None, None, None, None, None, None, None, None, None, None, None, None, None,
                        None, None, None, None, None, None, None, None, None, None, None, None, None,
                        None, None, None, None, None, None, None, None, None, None, None, None, None,
                        None, None, None)
    )


def test_generate_list_extra():
    _run_generation_comparison(
        configuration=LayoutConfiguration(seed_number=10000, logic=LayoutLogic.NO_GLITCHES, mode=LayoutMode.STANDARD,
                                          sky_temple_keys=LayoutRandomizedFlag.RANDOMIZED,
                                          item_loss=LayoutEnabledFlag.DISABLED, elevators=LayoutRandomizedFlag.VANILLA,
                                          hundo_guaranteed=LayoutEnabledFlag.DISABLED,
                                          difficulty=LayoutDifficulty.NORMAL),
        pickup_mapping=(24, 29, 49, 68, 57, 115, 23, 14, 92, 39, 3, 11, 20, 1, 52, 7, 98, 93, 79, 94, 88, 66, 74, 2,
                        114, 17, 118, 109, 5, 100, 106, 46, 18, 117, 91, 86, 35, 0, 47, 82, 10, 8, 9, 22, 112, 21, 33,
                        104, 101, 53, 15, 48, 45, 97, 77, 61, 81, 60, 67, 12, 41, 107, 19, 105, 28, 70, 99, 44, 63, 26,
                        65, 83, 87, 73, 71, 25, 78, 50, 16, 103, 59, 102, 13, 51, 96, 55, 64, 84, 111, 27, 80, 113, 72,
                        37, 90, 34, 54, 108, 69, 36, 43, 85, 30, 31, 116, 89, 40, 62, 76, 42, 95, 58, 75, 6, 38, 32,
                        110, 4, 56)
    )
