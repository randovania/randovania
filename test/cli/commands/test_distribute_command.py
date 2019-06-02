from pathlib import Path
from unittest.mock import patch, MagicMock, ANY

import randovania.cli.commands.distribute
from randovania.interface_common.cosmetic_patches import CosmeticPatches


@patch("randovania.interface_common.simplified_patcher.write_patcher_file_to_disk", autospec=True)
@patch("randovania.layout.permalink.Permalink.from_str")
@patch("randovania.generator.generator.generate_description", autospec=True)
def test_distribute_command_logic(mock_generate_description: MagicMock,
                                  mock_from_str: MagicMock,
                                  mock_write_patcher_file_to_disk: MagicMock,
                                  ):
    # Setup
    args = MagicMock()
    args.output_file = Path("asdfasdf/qwerqwerqwer/zxcvzxcv.json")
    patcher_json = Path("asdfasdf/qwerqwerqwer/zxcvzxcv.patcher-json")

    # Run
    randovania.cli.commands.distribute.distribute_command_logic(args)

    # Assert
    mock_from_str.assert_called_once_with(args.permalink)

    mock_generate_description.assert_called_once_with(
        permalink=mock_from_str.return_value,
        status_update=ANY,
        validate_after_generation=args.validate,
        timeout=None,
    )

    save_file_mock: MagicMock = mock_generate_description.return_value.save_to_file
    save_file_mock.assert_called_once_with(args.output_file)

    mock_write_patcher_file_to_disk.assert_called_once_with(
        patcher_json,
        mock_generate_description.return_value,
        CosmeticPatches.default(),
    )
