from unittest import mock
from unittest.mock import MagicMock, PropertyMock

from randovania.cli.commands import permalink_command
from randovania.layout.permalink import Permalink


@mock.patch("randovania.layout.permalink.Permalink.__new__", autospec=False)
@mock.patch("random.randint", autospec=True)
@mock.patch("randovania.interface_common.preset_manager.PresetManager.preset_for_name", autospec=True)
def test_permalink_logic(mock_preset_for_name: MagicMock,
                         mock_randint: MagicMock,
                         mock_permalink: MagicMock, ):
    # Setup
    args = MagicMock()
    args.seed_number = None
    args.preset = "Something"
    preset = mock_preset_for_name.return_value
    permalink = mock_permalink.return_value
    as_str_mock = PropertyMock()
    type(permalink).as_str = as_str_mock

    # Run
    permalink_command.permalink_command_logic(args)

    # Test
    mock_preset_for_name.assert_called_once_with(mock.ANY, "Something")
    mock_permalink.assert_called_once_with(Permalink, mock_randint.return_value,
                                           args.spoiler, preset)
    as_str_mock.assert_called_once_with()
