from __future__ import annotations

import json
import os
from unittest.mock import ANY, MagicMock, call

import pytest

from randovania.games.prime1.exporter.game_exporter import PrimeGameExporter, PrimeGameExportParams, adjust_model_names
from randovania.games.prime1.layout.prime_configuration import EnemyAttributeRandomizer


@pytest.mark.parametrize("use_echoes_models", [True, False])
@pytest.mark.parametrize("use_enemy_attribute_randomizer", [False, True])
def test_patch_game(mocker, tmp_path, use_echoes_models, use_enemy_attribute_randomizer):
    mock_symbols_for_file: MagicMock = mocker.patch(
        "py_randomprime.symbols_for_file",
        return_value={
            "UpdateHintState__13CStateManagerFf": 0x80044D38,
        },
    )
    seed = 103817502
    if use_enemy_attribute_randomizer:
        enemy_attribute_randomizer = EnemyAttributeRandomizer(
            1.4, 1.8, 2.25, 1.9, 0.2, 7.9, 10.6, 11.0, 0.1, 106.0, True
        ).as_json
    else:
        enemy_attribute_randomizer = None
    mock_patch_iso_raw: MagicMock = mocker.patch("py_randomprime.patch_iso_raw")
    mock_asset_convert: MagicMock = mocker.patch("randovania.patching.prime.asset_conversion.convert_prime2_pickups")
    mock_enemy_data: MagicMock = mocker.patch(
        "Random_Enemy_Attributes.Random_Enemy_Attributes.PyRandom_Enemy_Attributes"
    )
    mocker.patch("randovania.games.prime1.exporter.game_exporter.adjust_model_names")
    patch_data = {
        "_randovania_meta": {"layout_was_user_modified": True},
        "patch": "data",
        "gameConfig": {},
        "hasSpoiler": True,
        "preferences": {},
        "roomRandoMode": "None",
        "randEnemyAttributes": enemy_attribute_randomizer,
        "seed": seed,
    }
    progress_update = MagicMock()
    echoes_input_path = tmp_path.joinpath("echoes.iso")
    asset_cache_path = tmp_path.joinpath("internal_copies", "prime1", "prime2_models")

    if not use_echoes_models:
        asset_cache_path.mkdir(parents=True, exist_ok=True)

    exporter = PrimeGameExporter()

    # Run
    exporter.export_game(
        patch_data,
        PrimeGameExportParams(
            spoiler_output=None,
            input_path=tmp_path.joinpath("input.iso"),
            output_path=tmp_path.joinpath("output.iso"),
            echoes_input_path=echoes_input_path,
            asset_cache_path=asset_cache_path,
            use_echoes_models=use_echoes_models,
            cache_path=tmp_path.joinpath("cache_path"),
        ),
        progress_update,
    )

    # Assert
    expected = {
        "patch": "data",
        "gameConfig": {
            "updateHintStateReplacement": [
                148,
                33,
                255,
                204,
                124,
                8,
                2,
                166,
                144,
                1,
                0,
                56,
                191,
                193,
                0,
                44,
                124,
                127,
                27,
                120,
                136,
                159,
                0,
                2,
                44,
                4,
                0,
                0,
                64,
                130,
                0,
                24,
                187,
                193,
                0,
                44,
                128,
                1,
                0,
                56,
                124,
                8,
                3,
                166,
                56,
                33,
                0,
                52,
                78,
                128,
                0,
                32,
                128,
                127,
                8,
                112,
                44,
                3,
                0,
                0,
                65,
                130,
                255,
                228,
                128,
                3,
                0,
                8,
                44,
                0,
                0,
                0,
                65,
                129,
                255,
                216,
                63,
                192,
                128,
                4,
                99,
                222,
                77,
                164,
                56,
                128,
                1,
                96,
                124,
                4,
                247,
                172,
                44,
                4,
                0,
                0,
                56,
                132,
                255,
                224,
                64,
                130,
                255,
                244,
                124,
                0,
                4,
                172,
                76,
                0,
                1,
                44,
                56,
                192,
                0,
                0,
                152,
                223,
                0,
                2,
                187,
                193,
                0,
                44,
                128,
                1,
                0,
                56,
                124,
                8,
                3,
                166,
                56,
                33,
                0,
                52,
                78,
                128,
                0,
                32,
            ]
        },
        "preferences": {
            "cacheDir": os.fspath(tmp_path.joinpath("cache_path")),
        },
        "inputIso": os.fspath(tmp_path.joinpath("input.iso")),
        "outputIso": os.fspath(tmp_path.joinpath("output.iso")),
    }

    if use_echoes_models:
        expected["externAssetsDir"] = os.fspath(asset_cache_path)
        mock_asset_convert.assert_called_once_with(echoes_input_path, asset_cache_path, ANY)
    else:
        assert not asset_cache_path.exists()

    if use_enemy_attribute_randomizer:
        mock_enemy_data.assert_called_once_with(
            os.fspath(tmp_path.joinpath("input.iso")),
            os.fspath(tmp_path.joinpath("output.iso")),
            seed,
            1.4,
            1.8,
            2.25,
            1.9,
            0.2,
            7.9,
            10.6,
            11.0,
            0.1,
            106.0,
            True,
        )
    else:
        mock_enemy_data.assert_not_called()

    mock_symbols_for_file.assert_called_once_with(tmp_path.joinpath("input.iso"))
    mock_patch_iso_raw.assert_called_once_with(json.dumps(expected, indent=4, separators=(",", ": ")), ANY)


def test_adjust_model_names():
    # Setup
    patcher_data = {
        "levelData": {
            "Impact Crater": {
                "rooms": {
                    "A room": {
                        "pickups": [
                            {
                                "model": {"game": "prime1", "name": "Missile"},
                                "original_model": {"game": "prime1", "name": "Missile"},
                            },
                            {
                                "model": {"game": "prime1", "name": "Space Jump Boots"},
                                "original_model": {"game": "prime1", "name": "Space Jump Boots"},
                            },
                            {
                                "model": {"game": "prime2", "name": "Missile"},
                                "original_model": {"game": "prime2", "name": "MissileLauncher"},
                            },
                            {
                                "model": {"game": "prime2", "name": "Boost Ball"},
                                "original_model": {"game": "prime2", "name": "BoostBall"},
                            },
                            {
                                "model": {"game": "prime2", "name": "Spider Ball"},
                                "original_model": {"game": "prime2", "name": "SpiderBall"},
                            },
                            {
                                "model": {"game": "prime2", "name": "Nothing"},
                                "original_model": {"game": "prime2", "name": "DarkAmmoExpansion"},
                            },
                        ]
                    }
                }
            }
        }
    }

    asset_metadata = {"items": {"prime2_MissileLauncher": {}, "prime2_BoostBall": {}}}

    # Run
    adjust_model_names(patcher_data, asset_metadata, True)

    # Assert
    assert patcher_data == {
        "levelData": {
            "Impact Crater": {
                "rooms": {
                    "A room": {
                        "pickups": [
                            {"model": "Missile"},
                            {"model": "Space Jump Boots"},
                            {"model": "Missile"},
                            {"model": "prime2_BoostBall"},
                            {"model": "Spider Ball"},
                            {"model": "Nothing"},
                        ]
                    }
                }
            }
        }
    }


def test_room_rando_map_maker(test_files_dir, mocker, tmp_path):
    mock_symbols_for_file: MagicMock = mocker.patch(
        "py_randomprime.symbols_for_file",
        return_value={
            "UpdateHintState__13CStateManagerFf": 0x80044D38,
        },
    )
    mock_patch_iso_raw: MagicMock = mocker.patch("py_randomprime.patch_iso_raw")
    progress_update = MagicMock()

    mock_create_map_using_matplotlib: MagicMock = mocker.patch(
        "randovania.games.prime1.exporter.game_exporter.create_map_using_matplotlib"
    )

    patch_data = test_files_dir.read_json("patcher_data", "prime1", "prime1_crazy_seed", "world_1.json")

    exporter = PrimeGameExporter()

    # Run
    with pytest.raises(ValueError, match="Couldn't find output file.\nAborting Enemy Stat Randomizer"):
        exporter.export_game(
            patch_data,
            PrimeGameExportParams(
                spoiler_output=tmp_path,
                input_path=tmp_path.joinpath("input.iso"),
                output_path=tmp_path.joinpath("output.iso"),
                echoes_input_path=None,
                asset_cache_path=tmp_path.joinpath("asset_cache_path"),
                use_echoes_models=False,
                cache_path=tmp_path.joinpath("cache_path"),
            ),
            progress_update,
        )

    # Assert
    mock_symbols_for_file.assert_called_once_with(tmp_path.joinpath("input.iso"))
    mock_patch_iso_raw.assert_called_once_with(ANY, ANY)

    mock_create_map_using_matplotlib.assert_has_calls(
        [
            call(ANY, tmp_path.joinpath(f"output {x}.png"))
            for x in [
                "Chozo Ruins",
                "Impact Crater",
                "Phendrana Drifts",
                "Frigate Orpheon",
                "Magmoor Caverns",
                "Phazon Mines",
                "Tallon Overworld",
            ]
        ],
        any_order=True,
    )
