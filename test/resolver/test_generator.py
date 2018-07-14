from unittest.mock import MagicMock

from randovania.games.prime import binary_data
from randovania.resolver import generator, debug
from randovania.resolver.layout_configuration import LayoutConfiguration, LayoutLogic, LayoutMode, LayoutRandomizedFlag, \
    LayoutEnabledFlag, LayoutDifficulty
from randovania.resolver.layout_description import LayoutDescription


def _run_generation_comparison(
        configuration: LayoutConfiguration,
        pickup_mapping,
):
    debug._DEBUG_LEVEL = 0
    status_update = MagicMock()
    data = binary_data.decode_default_prime2()

    description = LayoutDescription(
        configuration=configuration,
        version='0.9.2',
        pickup_mapping=pickup_mapping,
        solver_path=())

    generated_description = generator.generate_list(data, configuration, status_update=status_update)

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
        pickup_mapping=(81, 14, 74, 29, 75, 102, 88, 106, 38, 118, 31, 82, 48, 113, 7, 67, 101, 15, 99, 117, 36, 23, 57,
                        89, 10, 66, 107, 45, 25, 49, 111, 93, 53, 35, 28, 51, 37, 73, 54, 97, 22, 77, 44, 80, 5, 104,
                        112, 33, 46, 100, 83, 76, 52, 62, 103, 17, 40, 58, 70, 4, 116, 98, 63, 32, 110, 71, 50, 69, 90,
                        91, 68, 19, 16, 11, 27, 6, 95, 56, 18, 79, 26, 12, 94, 84, 41, 96, 8, 2, 105, 114, 13, 65, 1,
                        87, 30, 109, 21, 64, 3, 34, 39, 92, 72, 55, 43, 59, 0, 24, 115, 108, 78, 86, 60, 42, 9, 20, 47,
                        85, 61)
    )


def test_generate_list_extra():
    _run_generation_comparison(
        configuration=LayoutConfiguration(seed_number=10000, logic=LayoutLogic.NO_GLITCHES, mode=LayoutMode.STANDARD,
                                          sky_temple_keys=LayoutRandomizedFlag.RANDOMIZED,
                                          item_loss=LayoutEnabledFlag.DISABLED, elevators=LayoutRandomizedFlag.VANILLA,
                                          hundo_guaranteed=LayoutEnabledFlag.DISABLED,
                                          difficulty=LayoutDifficulty.NORMAL),
        pickup_mapping=(99, 74, 103, 2, 6, 85, 37, 28, 12, 111, 44, 98, 115, 24, 97, 68, 11, 114, 42, 60, 89, 46, 34,
                        23, 84, 71, 59, 30, 1, 29, 35, 50, 104, 57, 55, 78, 20, 105, 52, 86, 14, 88, 49, 38, 9, 4, 66,
                        101, 80, 0, 36, 91, 107, 90, 62, 117, 70, 32, 7, 95, 113, 64, 76, 15, 77, 21, 92, 3, 100, 82,
                        65, 110, 18, 33, 109, 17, 10, 75, 118, 94, 83, 79, 8, 102, 19, 51, 54, 25, 27, 93, 5, 56, 39,
                        41, 47, 81, 67, 48, 13, 31, 69, 43, 53, 73, 116, 96, 106, 26, 22, 61, 16, 63, 108, 45, 40, 58,
                        112, 72, 87)
    )
