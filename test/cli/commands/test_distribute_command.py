from pathlib import Path
from unittest.mock import patch, MagicMock, ANY

import pytest

import randovania.cli.commands.distribute


@pytest.mark.parametrize("no_retry", [False, True])
def test_distribute_command_logic(no_retry: bool, mocker):
    # Setup
    mock_generate: MagicMock = mocker.patch("randovania.generator.generator.generate_description", autospec=True)
    mock_from_str: MagicMock = mocker.patch("randovania.layout.permalink.Permalink.from_str", autospec=True)

    args = MagicMock()
    args.output_file = Path("asdfasdf/qwerqwerqwer/zxcvzxcv.json")
    args.no_retry = no_retry
    extra_args = {}
    if no_retry:
        extra_args["attempts"] = 0

    # Run
    randovania.cli.commands.distribute.distribute_command_logic(args)

    # Assert
    mock_from_str.assert_called_once_with(args.permalink)

    mock_generate.assert_called_once_with(
        permalink=mock_from_str.return_value,
        status_update=ANY,
        validate_after_generation=args.validate,
        timeout=None,
        **extra_args,
    )

    save_file_mock: MagicMock = mock_generate.return_value.save_to_file
    save_file_mock.assert_called_once_with(args.output_file)
