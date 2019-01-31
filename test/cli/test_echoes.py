from pathlib import Path
from unittest.mock import patch, MagicMock, ANY

from randovania.cli import echoes
from randovania.layout.layout_configuration import LayoutConfiguration, LayoutTrickLevel, LayoutRandomizedFlag, \
    LayoutSkyTempleKeyMode
from randovania.layout.patcher_configuration import PatcherConfiguration
from randovania.layout.permalink import Permalink
from randovania.layout.starting_location import StartingLocation
from randovania.layout.starting_resources import StartingResources, StartingResourcesConfiguration


@patch("randovania.resolver.generator.generate_list", autospec=True)
def test_distribute_command_logic(mock_generate_list: MagicMock,
                                  ):
    # Setup
    args = MagicMock()
    args.trick_level = LayoutTrickLevel.HARD.value
    args.major_items_mode = False
    args.sky_temple_keys = LayoutSkyTempleKeyMode.ALL_BOSSES.value
    args.skip_item_loss = True
    args.seed = 15000
    args.output_file = "asdfasdf/qwerqwerqwer/zxcvzxcv.json"

    # Run
    echoes.distribute_command_logic(args)

    # Assert
    mock_generate_list.assert_called_once_with(
        permalink=Permalink(
            seed_number=args.seed,
            spoiler=True,
            patcher_configuration=PatcherConfiguration.default(),
            layout_configuration=LayoutConfiguration.from_params(
                trick_level=LayoutTrickLevel.HARD,
                sky_temple_keys=LayoutSkyTempleKeyMode.ALL_BOSSES,
                elevators=LayoutRandomizedFlag.VANILLA,
                pickup_quantities={},
                starting_location=StartingLocation.default(),
                starting_resources=StartingResources.from_non_custom_configuration(
                    StartingResourcesConfiguration.VANILLA_ITEM_LOSS_DISABLED),
            ),
        ),
        status_update=ANY
    )

    save_file_mock: MagicMock = mock_generate_list.return_value.save_to_file
    save_file_mock.assert_called_once_with(Path(args.output_file))
