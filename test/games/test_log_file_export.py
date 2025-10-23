from __future__ import annotations

import typing
from pathlib import Path

import pytest

import randovania
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.layout.layout_description import LayoutDescription
from randovania.lib import json_lib
from test.conftest import COOP_RDVGAMES, SOLO_RDVGAMES

if typing.TYPE_CHECKING:
    import _pytest.python
    import pytest_mock

    from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches
    from test.conftest import TestFilesDir


def _get_world_count(file_path: Path) -> int:
    # Across all rdvgame file versions, this field has always existed and been an array.
    data = json_lib.read_dict(file_path)
    return len(data["info"]["presets"])


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


@pytest.mark.benchmark
@pytest.mark.usefixtures("_mock_seed_hash")
def test_layout_patch_data_export(
    monkeypatch: pytest.MonkeyPatch,
    mocker: pytest_mock.MockerFixture,
    test_files_dir: TestFilesDir,
    layout_name: str,
    world_index: int,
    is_coop: bool,
) -> None:
    monkeypatch.setattr(randovania, "VERSION", "1.2.3")
    mock_attach = mocker.patch("randovania.exporter.patch_data_factory.PatchDataFactory._attach_to_sentry")

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
    mock_attach.assert_called_once_with()

    # _update_committed(data_path, cosmetic_path, data, cosmetic_patches)

    assert data == json_lib.read_path(data_path)


def pytest_generate_tests(metafunc: _pytest.python.Metafunc) -> None:
    log_dir = Path(__file__).parents[1].joinpath("test_files", "log_files")

    coop_names = {name for name, _ in COOP_RDVGAMES}
    layout_names = SOLO_RDVGAMES + COOP_RDVGAMES

    layouts = {layout_name: _get_world_count(log_dir.joinpath(layout_name)) for layout_name, _ in layout_names}

    metafunc.parametrize(
        ["layout_name", "world_index", "is_coop"],
        [
            (layout_name, world, layout_name in coop_names)
            for layout_name, world_count in layouts.items()
            for world in range(world_count)
        ],
    )
