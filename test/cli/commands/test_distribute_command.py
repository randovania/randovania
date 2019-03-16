from unittest.mock import patch, MagicMock, ANY

import randovania.cli.commands.distribute


@patch("randovania.layout.permalink.Permalink.from_str")
@patch("randovania.resolver.generator.generate_list", autospec=True)
def test_distribute_command_logic(mock_generate_list: MagicMock,
                                  mock_from_str: MagicMock,
                                  ):
    # Setup
    args = MagicMock()
    args.output_file = "asdfasdf/qwerqwerqwer/zxcvzxcv.json"

    # Run
    randovania.cli.commands.distribute.distribute_command_logic(args)

    # Assert
    mock_from_str.assert_called_once_with(args.permalink)

    mock_generate_list.assert_called_once_with(
        permalink=mock_from_str.return_value,
        status_update=ANY,
        validate_after_generation=True,
        timeout=None,
    )

    save_file_mock: MagicMock = mock_generate_list.return_value.save_to_file
    save_file_mock.assert_called_once_with(args.output_file)
