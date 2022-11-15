import json
from unittest.mock import MagicMock, ANY

import pytest

from randovania.games.prime2.exporter.game_exporter import EchoesGameExporter, EchoesGameExportParams, \
    decode_randomizer_data


@pytest.mark.parametrize("has_input_iso", [False, True])
@pytest.mark.parametrize("use_prime_models", [False, True])
@pytest.mark.parametrize("use_new_patcher", [False, True])
@pytest.mark.parametrize("use_hud_color", [False, True])
def test_do_export_game(mocker, tmp_path, has_input_iso, use_hud_color, use_new_patcher, use_prime_models):
    input_path = MagicMock() if has_input_iso else None

    mock_patch_banner: MagicMock = mocker.patch(
        "randovania.patching.patchers.gamecube.banner_patcher.patch_game_name_and_id")
    mock_unpack_iso: MagicMock = mocker.patch("randovania.patching.patchers.gamecube.iso_packager.unpack_iso")
    mock_pack_iso: MagicMock = mocker.patch("randovania.patching.patchers.gamecube.iso_packager.pack_iso")
    mock_create_backup: MagicMock = mocker.patch("randovania.games.prime2.patcher.claris_randomizer.create_pak_backups")
    mock_restore_backup: MagicMock = mocker.patch(
        "randovania.games.prime2.patcher.claris_randomizer.restore_pak_backups")
    mock_apply_patcher: MagicMock = mocker.patch(
        "randovania.games.prime2.patcher.claris_randomizer.apply_patcher_file")
    mock_patch_paks: MagicMock = mocker.patch("open_prime_rando.echoes_patcher.patch_paks")
    mock_mp2hudcolor_c: MagicMock = mocker.patch("mp2hudcolor.mp2hudcolor_c")
    mock_convert_prime1: MagicMock = mocker.patch("randovania.patching.prime.asset_conversion.convert_prime1_pickups")

    exporter = EchoesGameExporter()
    new_patcher_data = {
        "rasdfasdfasdfsd": True,
    }
    patch_data = {
        "shareable_hash": "asdf",
        "publisher_id": "ABCD",
        "pickups": [],
        "menu_mod": False,
        "specific_patches": {
            "hud_color": [0, 255, 127] if use_hud_color else None,
        },
        "new_patcher": new_patcher_data if use_new_patcher else None,
    }
    patch_data_str = json.dumps(patch_data, indent=4)

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
    mock_patch_banner.assert_called_once_with(
        export_params.contents_files_path,
        "Metroid Prime 2: Randomizer - {}".format(patch_data["shareable_hash"]),
        patch_data["publisher_id"]
    )

    if use_prime_models:
        mock_convert_prime1.assert_called_once_with(
            export_params.prime_path, export_params.contents_files_path, export_params.asset_cache_path,
            patch_data, decode_randomizer_data(), ANY,
        )
    else:
        mock_convert_prime1.assert_not_called()

    mock_apply_patcher.assert_called_once_with(
        export_params.contents_files_path,
        patch_data,
        decode_randomizer_data(),
        ANY,
    )

    if use_new_patcher:
        mock_patch_paks.assert_called_once_with(
            ANY,  # PathFileProvider(export_params.contents_files_path),
            export_params.contents_files_path,
            new_patcher_data,
        )
    else:
        mock_patch_paks.assert_not_called()

    if use_hud_color:
        ntwk_file = str(export_params.contents_files_path.joinpath("files", "Standard.ntwk"))
        mock_mp2hudcolor_c.assert_called_once_with(
            ntwk_file, ntwk_file, 0, 1, 127 / 255
        )
    else:
        mock_mp2hudcolor_c.assert_not_called()

    mock_pack_iso.assert_called_once_with(
        iso=export_params.output_path,
        game_files_path=export_params.contents_files_path,
        progress_update=ANY,
    )
