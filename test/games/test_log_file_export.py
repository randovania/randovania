from __future__ import annotations

import typing
from pathlib import Path

import pytest

import randovania
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.layout.layout_description import LayoutDescription
from randovania.lib import json_lib

if typing.TYPE_CHECKING:
    import _pytest.python
    from conftest import TestFilesDir

    from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches


def _update_committed(data_path: Path, cosmetic_path: Path, data: dict, cosmetic_patches: BaseCosmeticPatches) -> None:
    """
    Updates the files that are used as reference value for later runs. Make sure to always keep this call commented out.
    """
    json_lib.write_path(data_path, data)

    if cosmetic_patches != type(cosmetic_patches)():
        # If not the default
        json_lib.write_path(cosmetic_path, cosmetic_patches.as_json)
    else:
        cosmetic_path.unlink(missing_ok=True)

    raise NotImplementedError("This function should not be called in normal execution.")


@pytest.mark.usefixtures("_mock_seed_hash")
def test_layout_patch_data_export(
    monkeypatch: pytest.MonkeyPatch,
    test_files_dir: TestFilesDir,
    layout_name: str,
    world_index: int,
    is_coop: bool,
) -> None:
    monkeypatch.setattr(randovania, "VERSION", "1.2.3")

    layout = LayoutDescription.from_file(test_files_dir.joinpath("log_files", layout_name))
    game_enum = layout.get_preset(world_index).game

    layout_path = layout_name.replace(".rdvgame", "")
    if layout.world_count > 0:
        layout_path += f"/world_{world_index + 1}"

    data_path = test_files_dir.joinpath("patcher_data", game_enum.value, f"{layout_path}.json")
    cosmetic_path = data_path.with_name(f"cosmetic_{world_index + 1}.json")

    if cosmetic_path.exists():
        cosmetic_patches = game_enum.data.layout.cosmetic_patches.from_json(json_lib.read_dict(cosmetic_path))
    else:
        cosmetic_patches = game_enum.data.layout.cosmetic_patches()

    factory = game_enum.patch_data_factory(
        description=layout,
        players_config=PlayersConfiguration(
            player_index=world_index,
            player_names={i: f"World {i + 1}" for i in range(layout.world_count)},
            is_coop=is_coop,
        ),
        cosmetic_patches=cosmetic_patches,
    )

    data = factory.create_data()

    # _update_committed(data_path, cosmetic_path, data, cosmetic_patches)

    assert data == json_lib.read_path(data_path)


def _get_world_count(file_path: Path) -> int:
    # Across all rdvgame file versions, this field has always existed and been an array.
    data = json_lib.read_dict(file_path)
    return len(data["info"]["presets"])


def pytest_generate_tests(metafunc: _pytest.python.Metafunc) -> None:
    log_dir = Path(__file__).parents[1].joinpath("test_files", "log_files")

    solo_names = [
        # Cross Game Multis
        "multi-cs+dread+prime1+prime2.rdvgame",
        "multi-am2r+cs+dread+prime1+prime2.rdvgame",
        "multi-am2r+cs+dread+prime1+prime2+msr.rdvgame",
        "prime1_and_2_multi.rdvgame",
        "cs_echoes_multi_1.rdvgame",
        "dread_prime1_multiworld.rdvgame",  # dread-prime1 multi
        # AM2R
        "am2r/starter_preset.rdvgame",  # starter preset
        "am2r/door_lock.rdvgame",  # starter preset+door lock rando
        "am2r/door_lock_open.rdvgame",  # starter preset+door lock rando with open transitions
        "am2r/progressive_items.rdvgame",  # Starter preset+progressive items
        "am2r/starting_items.rdvgame",  # Starter preset + random starting items
        "am2r/transport_pipe_shuffle.rdvgame",  # Starter preset + shuffled transport pipes
        "am2r/custom_dna_required.rdvgame",  # Has 20/30 dna
        "am2r/chaos_options.rdvgame",  # Has Chaos Options
        # Blank
        "blank/issue-3717.rdvgame",
        # Factorio
        "factorio/starter_preset.rdvgame",
        # Fusion
        "fusion/starter_preset.rdvgame",
        "fusion/short_intro.rdvgame",
        # Dread
        "dread/starter_preset.rdvgame",  # starter preset
        "dread/crazy_settings.rdvgame",  # crazy settings
        "dread/dread_dread_multiworld.rdvgame",  # dread-dread multi
        "dread/elevator_rando.rdvgame",  # elevator_rando multi
        "dread/custom_start.rdvgame",  # crazy settings
        "dread/custom_patcher_data.rdvgame",  # custom patcher data
        "dread/all_settings.rdvgame",  # all settings enabled
        "dread/hide_all_with_nothing.rdvgame",  # Model+scan+name hidden with nothing data
        # Planets (Zebeth)
        "planets_zebeth/starter_preset.rdvgame",  # starter preset (vanilla keys)
        "planets_zebeth/starter_preset_shuffle_keys.rdvgame",  # starter preset (shuffled keys)
        # Prime 1
        "prime1_crazy_seed.rdvgame",  # chaos features
        "prime1_crazy_seed_one_way_door.rdvgame",  # same as above but 1-way doors
        "prime1_refills.rdvgame",  # Refill items + custom artifact count
        # Samus Returns
        "samus_returns/arachnus_boss_start_inventory.rdvgame",  # arachnus final boss + starting inventory + export ids
        "samus_returns/diggernaut_boss_free_placement_dna.rdvgame",  # diggernaut final boss + 7/15 dna anywhere
        "samus_returns/door_lock.rdvgame",  # starter preset + door lock
        "samus_returns/door_lock_access_open.rdvgame",  # door lock + access open doors
        "samus_returns/queen_boss_custom_required_dna.rdvgame",  # quuen final boss + custom required dna 20/30
        "samus_returns/starter_preset.rdvgame",  # starter preset
        # Super Metroid
        "sdm_test_game.rdvgame",
    ]

    coop_names = [
        "multi_coop_am2r+bdg+cs+dread+prime1+echoes+msr.rdvgame",
    ]

    layout_names = solo_names + coop_names

    layouts = {layout_name: _get_world_count(log_dir.joinpath(layout_name)) for layout_name in layout_names}

    metafunc.parametrize(
        ["layout_name", "world_index", "is_coop"],
        [
            (layout_name, world, layout_name in coop_names)
            for layout_name, world_count in layouts.items()
            for world in range(world_count)
        ],
    )
