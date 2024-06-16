from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import ANY, MagicMock, call

import pytest

import randovania.cli.commands.generate
from randovania.games.game import RandovaniaGame
from randovania.generator import generator
from randovania.layout.generator_parameters import GeneratorParameters
from randovania.layout.versioned_preset import VersionedPreset

if TYPE_CHECKING:
    import pytest_mock
    from conftest import TestFilesDir

    from randovania.interface_common.preset_manager import PresetManager


@pytest.mark.parametrize("repeat", [1, 2])
@pytest.mark.parametrize("add_preset_file", [False, True])
@pytest.mark.parametrize("preset_name", [None, "Starter Preset"])
@pytest.mark.parametrize("no_retry", [False, True])
def test_generate_logic(
    no_retry: bool,
    preset_name: str | None,
    add_preset_file: bool,
    repeat: int,
    mocker: pytest_mock.MockerFixture,
    preset_manager: PresetManager,
    test_files_dir: TestFilesDir,
) -> None:
    # Setup
    layout_description = MagicMock()
    mock_run = mocker.patch("asyncio.run", return_value=layout_description)
    mock_generate = mocker.patch(
        "randovania.generator.generator.generate_and_validate_description", new_callable=MagicMock
    )
    mock_from_str: MagicMock = mocker.patch("randovania.layout.permalink.Permalink.from_str", autospec=True)
    test_preset_file = test_files_dir.joinpath("presets", "super_test_preset.rdvpreset")

    args = MagicMock()
    args.output_file = Path("asdfasdf/qwerqwerqwer/zxcvzxcv.json")
    args.no_retry = no_retry
    args.repeat = repeat

    if preset_name is None and not add_preset_file:
        # Permalink
        args.permalink = "<the permalink>"
        mock_from_str.return_value.seed_hash = b"12345"
    else:
        args.name = [f"prime2/{preset_name}"] if preset_name else []
        args.file = [test_preset_file] if add_preset_file else []

        args.seed_number = 0
        args.race = False
        args.development = False

    attempts = generator.DEFAULT_ATTEMPTS
    if no_retry:
        attempts = 0

    if preset_name is None and not add_preset_file:
        generator_params: GeneratorParameters = mock_from_str.return_value.parameters
    else:
        args.permalink = None
        presets = []
        if preset_name:
            presets.append(
                preset_manager.included_preset_with(RandovaniaGame.METROID_PRIME_ECHOES, preset_name).get_preset()
            )
        if add_preset_file:
            presets.append(VersionedPreset.from_file_sync(test_preset_file).get_preset())
        generator_params = GeneratorParameters(0, True, presets)

    # Run
    if preset_name is None and not add_preset_file:
        randovania.cli.commands.generate.generate_from_permalink_logic(args)
    else:
        randovania.cli.commands.generate.generate_from_preset_logic(args)

    # Assert
    if preset_name is None and not add_preset_file:
        mock_from_str.assert_called_once_with(args.permalink)
    else:
        mock_from_str.assert_not_called()

    mock_generate.assert_has_calls(
        [
            call(
                generator_params=generator_params,
                status_update=ANY,
                validate_after_generation=args.validate,
                timeout=None,
                attempts=attempts,
            )
        ]
        * repeat
    )
    mock_run.assert_has_calls([call(mock_generate.return_value)] * repeat)

    save_file_mock: MagicMock = layout_description.save_to_file
    save_file_mock.assert_called_once_with(args.output_file)
