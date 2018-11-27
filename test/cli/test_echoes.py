from unittest.mock import patch, MagicMock, ANY

from randovania.cli import echoes
from randovania.resolver.layout_configuration import LayoutConfiguration, LayoutTrickLevel, LayoutMode, LayoutRandomizedFlag, \
    LayoutEnabledFlag, LayoutDifficulty


@patch("randovania.cli.prime_database.decode_data_file", autospec=True)
@patch("randovania.resolver.generator.generate_list", autospec=True)
def test_distribute_command_logic(mock_generate_list: MagicMock,
                                  mock_decode_data_file: MagicMock,
                                  ):
    # Setup
    args = MagicMock()
    args.trick_level = LayoutTrickLevel.HARD.value
    args.major_items_mode = False
    args.vanilla_sky_temple_keys = False
    args.skip_item_loss = True
    args.seed = 15000

    # Run
    echoes.distribute_command_logic(args)

    # Assert
    mock_decode_data_file.assert_called_once_with(args)
    mock_generate_list.assert_called_once_with(
        data=mock_decode_data_file.return_value,
        seed_number=args.seed,
        configuration=LayoutConfiguration(
            trick_level=LayoutTrickLevel.HARD,
            mode=LayoutMode.STANDARD,
            sky_temple_keys=LayoutRandomizedFlag.RANDOMIZED,
            item_loss=LayoutEnabledFlag.DISABLED,
            elevators=LayoutRandomizedFlag.VANILLA,
            hundo_guaranteed=LayoutEnabledFlag.DISABLED,
            difficulty=LayoutDifficulty.NORMAL,
            pickup_quantities={}
        ),
        status_update=ANY
    )

    save_file_mock: MagicMock = mock_generate_list.return_value.save_to_file
    save_file_mock.assert_called_once_with(args.output_file)
