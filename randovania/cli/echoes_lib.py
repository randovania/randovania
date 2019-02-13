from randovania.layout.layout_configuration import LayoutTrickLevel, LayoutSkyTempleKeyMode, LayoutConfiguration, \
    LayoutRandomizedFlag
from randovania.layout.starting_location import StartingLocation
from randovania.layout.starting_resources import StartingResources


def add_debug_argument(parser):
    parser.add_argument(
        "--debug",
        choices=range(4),
        type=int,
        default=0,
        help="The level of debug logging to print.")


def add_layout_configuration_arguments(parser):
    parser.add_argument(
        "--trick-level",
        type=str,
        choices=[layout.value for layout in LayoutTrickLevel],
        default=LayoutTrickLevel.NO_TRICKS.value,
        help="The level of tricks to use.")
    parser.add_argument(
        "--sky-temple-keys",
        type=str,
        choices=[mode.value for mode in LayoutSkyTempleKeyMode],
        default=LayoutSkyTempleKeyMode.FULLY_RANDOM.value,
        help="The Sky Temple Keys randomization mode.")
    parser.add_argument(
        "--skip-item-loss",
        action="store_true",
        help="Disables the item loss cutscene, disabling losing your items."
    )


def get_layout_configuration_from_args(args) -> LayoutConfiguration:
    return LayoutConfiguration.from_params(
        trick_level=LayoutTrickLevel(args.trick_level),
        sky_temple_keys=LayoutSkyTempleKeyMode(args.sky_temple_keys),
        elevators=LayoutRandomizedFlag.VANILLA,
        pickup_quantities={},
        starting_location=StartingLocation.default(),
        starting_resources=StartingResources.from_item_loss(not args.skip_item_loss),
    )
