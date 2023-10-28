from __future__ import annotations

import typing
from pathlib import Path
from unittest.mock import PropertyMock

import randovania
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.layout.layout_description import LayoutDescription
from randovania.lib import json_lib

if typing.TYPE_CHECKING:
    import _pytest.python
    import pytest
    import pytest_mock
    from conftest import TestFilesDir


def test_layout_patch_data_export(
    monkeypatch: pytest.MonkeyPatch,
    mocker: pytest_mock.MockerFixture,
    test_files_dir: TestFilesDir,
    layout_name: str,
    world_index: int,
) -> None:
    monkeypatch.setattr(randovania, "VERSION", "1.2.3")
    mocker.patch(
        "randovania.layout.layout_description.LayoutDescription.shareable_word_hash",
        new_callable=PropertyMock,
        return_value="Some Words",
    )
    mocker.patch(
        "randovania.layout.layout_description.LayoutDescription.shareable_hash",
        new_callable=PropertyMock,
        return_value="XXXXXXXX",
    )

    layout = LayoutDescription.from_file(test_files_dir.joinpath("log_files", layout_name))

    game_enum = layout.get_preset(world_index).game
    factory = game_enum.patch_data_factory(
        description=layout,
        players_config=PlayersConfiguration(
            player_index=world_index, player_names={i: f"World {i + 1}" for i in range(layout.world_count)}
        ),
        cosmetic_patches=game_enum.data.layout.cosmetic_patches(),
    )

    data = factory.create_data()

    layout_path = layout_name.replace(".rdvgame", "")
    if layout.world_count > 0:
        layout_path += f"/world_{world_index + 1}"

    data_path = test_files_dir.joinpath("patcher_data", game_enum.value, f"{layout_path}.json")

    # json_lib.write_path(data_path, data); assert False

    assert data == json_lib.read_path(data_path)


def pytest_generate_tests(metafunc: _pytest.python.Metafunc) -> None:
    log_dir = Path(__file__).parents[1].joinpath("test_files", "log_files")

    layout_name = "all_game_multi.rdvgame"
    layout = LayoutDescription.from_file(log_dir.joinpath(layout_name))

    metafunc.parametrize(["layout_name", "world_index"], [(layout_name, world) for world in range(layout.world_count)])
