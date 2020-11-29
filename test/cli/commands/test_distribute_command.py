from pathlib import Path
from unittest.mock import MagicMock, ANY

import pytest

import randovania.cli.commands.distribute
from randovania.layout.permalink import Permalink


@pytest.mark.parametrize("preset_name", [None, "Starter Preset"])
@pytest.mark.parametrize("no_retry", [False, True])
def test_distribute_command_logic(no_retry: bool, preset_name: str, mocker, preset_manager):
    # Setup
    mock_generate: MagicMock = mocker.patch("randovania.generator.generator.generate_description", autospec=True)
    mock_from_str: MagicMock = mocker.patch("randovania.layout.permalink.Permalink.from_str", autospec=True)

    args = MagicMock()
    args.output_file = Path("asdfasdf/qwerqwerqwer/zxcvzxcv.json")
    args.no_retry = no_retry
    args.preset_name = preset_name
    args.seed_number = 0
    extra_args = {}
    if no_retry:
        extra_args["attempts"] = 0

    if preset_name is None:
        permalink = mock_from_str.return_value
    else:
        args.permalink = None
        permalink = Permalink(0, True, {0: preset_manager.preset_for_name(preset_name).get_preset()})

    # Run
    randovania.cli.commands.distribute.distribute_command_logic(args)

    # Assert
    if preset_name is None:
        mock_from_str.assert_called_once_with(args.permalink)
    else:
        mock_from_str.assert_not_called()

    mock_generate.assert_called_once_with(
        permalink=permalink,
        status_update=ANY,
        validate_after_generation=args.validate,
        timeout=None,
        **extra_args,
    )

    save_file_mock: MagicMock = mock_generate.return_value.save_to_file
    save_file_mock.assert_called_once_with(args.output_file)
