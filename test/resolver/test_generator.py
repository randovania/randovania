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
    debug._DEBUG_LEVEL = 0
    status_update = MagicMock()
    game = data_reader.decode_data(binary_data.decode_default_prime2(), [])

    description = LayoutDescription(
        configuration=configuration,
        version='0.9.2',
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
        pickup_mapping=(
            86, 68, 14, 53, 44, 1, 23, 13, 45, 8, 7, 106, 118, 115, 87, 107, 18, 74, 79, 105, 37, 60, 82, 73, 116, 113,
            88, 62, 24, 92, 46, 11, 29, 117, 43, 51, 39, 89, 58, 47, 52, 112, 94, 76, 56, 78, 81, 40, 12, 15, 91, 111,
            19, 42, 4, 97, 96, 57, 32, 75, 30, 61, 50, 108, 102, 114, 38, 80, 25, 98, 27, 21, 110, 85, 63, 48, 17, 2,
            49, 99, 34, 103, 71, 65, 9, 41, 64, 66, 72, 84, 109, 35, 95, 36, 20, 90, 16, 5, 100, 33, 26, 22, 10, 101,
            55, 93, 31, 6, 77, 0, 67, 3, 70, 59, 69, 54, 104, 83, 28)
    )
