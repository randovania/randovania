from unittest.mock import patch, MagicMock

import randovania.cli.commands.create_permalink
from randovania.layout.layout_configuration import LayoutConfiguration, LayoutElevators, \
    LayoutSkyTempleKeyMode
from randovania.layout.patcher_configuration import PatcherConfiguration
from randovania.layout.permalink import Permalink
from randovania.layout.starting_location import StartingLocation
from randovania.layout.trick_level import LayoutTrickLevel, TrickLevelConfiguration


@patch("randovania.cli.commands.create_permalink._print_permalink", autospec=True)
def test_create_permalink_logic(mock_print: MagicMock,
                                ):
    # Setup
    args = MagicMock()
    args.trick_level = LayoutTrickLevel.HARD.value
    args.major_items_mode = False
    args.sky_temple_keys = LayoutSkyTempleKeyMode.ALL_BOSSES.value
    args.skip_item_loss = True
    args.seed = 15000
    args.menu_mod = False
    args.warp_to_start = False

    # Run
    randovania.cli.commands.create_permalink.create_permalink_logic(args)

    # Assert
    permalink = Permalink(
        seed_number=args.seed,
        spoiler=True,
        patcher_configuration=PatcherConfiguration(
            menu_mod=args.menu_mod,
            warp_to_start=args.warp_to_start,
        ),
        layout_configuration=LayoutConfiguration.from_params(
            trick_level_configuration=TrickLevelConfiguration(LayoutTrickLevel.HARD),
            sky_temple_keys=LayoutSkyTempleKeyMode.ALL_BOSSES,
            elevators=LayoutElevators.VANILLA,
            starting_location=StartingLocation.default(),
        ),
    )

    # Assert
    mock_print.assert_called_once_with(permalink)
