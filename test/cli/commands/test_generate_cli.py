from pathlib import Path
from typing import Optional

import pytest
from mock import MagicMock, ANY, AsyncMock

import randovania.cli.commands.generate
from randovania.games.game import RandovaniaGame
from randovania.layout.generator_parameters import GeneratorParameters


@pytest.mark.parametrize("preset_name", [None, "Starter Preset"])
@pytest.mark.parametrize("no_retry", [False, True])
def test_generate_logic(no_retry: bool, preset_name: Optional[str], mocker, preset_manager):
    # Setup
    mock_generate: AsyncMock = mocker.patch("randovania.generator.generator.generate_and_validate_description",
                                            new_callable=AsyncMock)
    mock_generate.return_value = MagicMock()
    mock_from_str: MagicMock = mocker.patch("randovania.layout.permalink.Permalink.from_str", autospec=True)

    args = MagicMock()
    args.output_file = Path("asdfasdf/qwerqwerqwer/zxcvzxcv.json")
    args.no_retry = no_retry

    if preset_name is None:
        # Permalink
        args.permalink = "<the permalink>"
    else:
        args.game = RandovaniaGame.METROID_PRIME_ECHOES.value
        args.preset_name = [preset_name]
        args.seed_number = 0
        args.race = False

    extra_args = {}
    if no_retry:
        extra_args["attempts"] = 0

    if preset_name is None:
        generator_params: GeneratorParameters = mock_from_str.return_value.parameters
    else:
        args.permalink = None
        preset = preset_manager.included_preset_with(RandovaniaGame.METROID_PRIME_ECHOES, preset_name).get_preset()
        generator_params = GeneratorParameters(0, True, [preset])

    # Run
    if preset_name is None:
        randovania.cli.commands.generate.generate_from_permalink_logic(args)
    else:
        randovania.cli.commands.generate.generate_from_preset_logic(args)

    # Assert
    if preset_name is None:
        mock_from_str.assert_called_once_with(args.permalink)
    else:
        mock_from_str.assert_not_called()

    mock_generate.assert_awaited_once_with(
        generator_params=generator_params,
        status_update=ANY,
        validate_after_generation=args.validate,
        timeout=None,
        **extra_args,
    )

    save_file_mock: MagicMock = mock_generate.return_value.save_to_file
    save_file_mock.assert_called_once_with(args.output_file)
