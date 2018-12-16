from pathlib import Path
from unittest.mock import patch, MagicMock, ANY

from randovania.cli import echoes
from randovania.resolver.layout_configuration import LayoutConfiguration, LayoutTrickLevel, LayoutRandomizedFlag, \
    LayoutEnabledFlag
from randovania.resolver.patcher_configuration import PatcherConfiguration
from randovania.resolver.permalink import Permalink


@patch("randovania.resolver.generator.generate_list", autospec=True)
def test_distribute_command_logic(mock_generate_list: MagicMock,
                                  ):
    # Setup
    args = MagicMock()
    args.trick_level = LayoutTrickLevel.HARD.value
    args.major_items_mode = False
    args.vanilla_sky_temple_keys = False
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
                sky_temple_keys=LayoutRandomizedFlag.RANDOMIZED,
                item_loss=LayoutEnabledFlag.DISABLED,
                elevators=LayoutRandomizedFlag.VANILLA,
                pickup_quantities={}
            ),
        ),
        status_update=ANY
    )

    save_file_mock: MagicMock = mock_generate_list.return_value.save_to_file
    save_file_mock.assert_called_once_with(Path(args.output_file))
