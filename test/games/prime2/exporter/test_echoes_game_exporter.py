from __future__ import annotations

import json
from typing import TYPE_CHECKING
from unittest.mock import ANY, MagicMock

import pytest

from randovania.games.prime2.exporter.claris_randomizer_data import decode_randomizer_data
from randovania.games.prime2.exporter.export_params import EchoesGameExportParams
from randovania.games.prime2.exporter.game_exporter import (
    EchoesGameExporter,
)
from randovania.patching.patchers.exceptions import UnableToExportError

if TYPE_CHECKING:
    from pathlib import Path

    import pytest_mock


def test_do_export_broken_internal_copy(tmp_path: Path):
    patch_data = {
        "menu_mod": False,
    }

    export_params = EchoesGameExportParams(
        input_path=None,
        output_path=MagicMock(),
        contents_files_path=tmp_path.joinpath("contents"),
        asset_cache_path=tmp_path.joinpath("asset_cache_path"),
        backup_files_path=tmp_path.joinpath("backup"),
        prime_path=MagicMock(),
        use_prime_models=False,
        spoiler_output=None,
    )
    progress_update = MagicMock()
    exporter = EchoesGameExporter()

    # Run
    with pytest.raises(UnableToExportError):
        exporter._do_export_game(patch_data, export_params, progress_update)


@pytest.mark.parametrize("has_input_iso", [False, True])
@pytest.mark.parametrize("use_prime_models", [False, True])
@pytest.mark.parametrize("use_new_patcher", [False, True])
@pytest.mark.parametrize("use_hud_color", [False, True])
@pytest.mark.parametrize("use_menu_mod", [False, True])
def test_do_export_game(
    mocker: pytest_mock.MockerFixture,
    tmp_path,
    has_input_iso,
    use_hud_color,
    use_new_patcher,
    use_prime_models,
    use_menu_mod,
):
    input_path = MagicMock() if has_input_iso else None

    mock_patch_banner = mocker.patch("randovania.patching.patchers.gamecube.banner_patcher.patch_game_name_and_id")
    mock_unpack_iso = mocker.patch("randovania.patching.patchers.gamecube.iso_packager.unpack_iso")
    mock_pack_iso = mocker.patch("randovania.patching.patchers.gamecube.iso_packager.pack_iso")
    mock_create_backup = mocker.patch("randovania.games.prime2.patcher.claris_randomizer.create_pak_backups")
    mock_restore_backup = mocker.patch("randovania.games.prime2.patcher.claris_randomizer.restore_pak_backups")
    mock_apply_patcher = mocker.patch("randovania.games.prime2.patcher.claris_randomizer.apply_patcher_file")
    mock_patch_paks = mocker.patch("open_prime_rando.echoes_patcher.patch_paks")
    mock_mp2hudcolor_c = mocker.patch("mp2hudcolor.mp2hudcolor_c")
    mock_convert_prime1 = mocker.patch("randovania.patching.prime.asset_conversion.convert_prime1_pickups")
    mock_menu_mod = mocker.patch("randovania.games.prime2.patcher.claris_randomizer.add_menu_mod_to_files")
    mock_coin_chest = mocker.patch("randovania.games.prime2.exporter.game_exporter.copy_coin_chest")

    mock_dol_file = mocker.patch("ppc_asm.dol_file.DolFile")
    mock_apply_dol = mocker.patch("open_prime_rando.dol_patching.echoes.dol_patcher.apply_patches")
    mock_dol_patches_from_json = mocker.patch(
        "open_prime_rando.dol_patching.echoes.dol_patcher.EchoesDolPatchesData.from_json"
    )

    exporter = EchoesGameExporter()
    new_patcher_data = {
        "rasdfasdfasdfsd": True,
    }
    patch_data = {
        "banner_name": "the_name",
        "publisher_id": "ABCD",
        "pickups": [],
        "menu_mod": use_menu_mod,
        "dol_patches": "old_dol_patches",
        "specific_patches": {
            "hud_color": [0, 255, 127] if use_hud_color else None,
        },
    }

    patch_data_str = json.dumps(patch_data, indent=4)

    if use_new_patcher:
        patch_data["new_patcher"] = new_patcher_data

    export_params = EchoesGameExportParams(
        input_path=input_path,
        output_path=MagicMock(),
        contents_files_path=tmp_path.joinpath("contents"),
        asset_cache_path=tmp_path.joinpath("asset_cache_path"),
        backup_files_path=tmp_path.joinpath("backup"),
        prime_path=MagicMock(),
        use_prime_models=use_prime_models,
        spoiler_output=None,
    )
    progress_update = MagicMock()

    # Run
    exporter._do_export_game(patch_data, export_params, progress_update)

    # Assert
    if input_path is not None:
        mock_unpack_iso.assert_called_once_with(
            iso=export_params.input_path,
            game_files_path=export_params.contents_files_path,
            progress_update=ANY,
        )
        mock_create_backup.assert_called_once_with(
            export_params.contents_files_path,
            export_params.backup_files_path,
            ANY,
        )
        mock_restore_backup.assert_not_called()
    else:
        mock_unpack_iso.assert_not_called()
        mock_create_backup.assert_not_called()
        mock_restore_backup.assert_called_once_with(
            export_params.contents_files_path,
            export_params.backup_files_path,
            ANY,
        )

    assert export_params.contents_files_path.joinpath("files", "patcher_data.json").read_text() == patch_data_str
    mock_patch_banner.assert_called_once_with(export_params.contents_files_path, "the_name", patch_data["publisher_id"])

    if use_prime_models:
        mock_convert_prime1.assert_called_once_with(
            export_params.prime_path,
            export_params.contents_files_path,
            export_params.asset_cache_path,
            patch_data,
            decode_randomizer_data(),
            ANY,
        )
    else:
        mock_convert_prime1.assert_not_called()

    mock_coin_chest.assert_called_once_with(export_params.contents_files_path)

    mock_apply_patcher.assert_called_once_with(
        export_params.contents_files_path,
        patch_data,
        decode_randomizer_data(),
        ANY,
    )

    mock_dol_file.assert_called_once_with(export_params.contents_files_path.joinpath("sys", "main.dol"))
    mock_dol_patches_from_json.assert_called_once_with("old_dol_patches")
    mock_apply_dol.assert_called_once_with(mock_dol_file.return_value, mock_dol_patches_from_json.return_value)

    if use_new_patcher:
        mock_patch_paks.assert_called_once_with(
            ANY,  # PathFileProvider(export_params.contents_files_path),
            export_params.contents_files_path,
            new_patcher_data,
            ANY,  # status update
        )
    else:
        mock_patch_paks.assert_not_called()

    if use_hud_color:
        ntwk_file = str(export_params.contents_files_path.joinpath("files", "Standard.ntwk"))
        mock_mp2hudcolor_c.assert_called_once_with(ntwk_file, ntwk_file, 0, 1, 127 / 255)
    else:
        mock_mp2hudcolor_c.assert_not_called()

    if use_menu_mod:
        mock_menu_mod.assert_called_once_with(export_params.contents_files_path, ANY)
    else:
        mock_menu_mod.assert_not_called()

    mock_pack_iso.assert_called_once_with(
        iso=export_params.output_path,
        game_files_path=export_params.contents_files_path,
        progress_update=ANY,
    )
