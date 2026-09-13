from __future__ import annotations

import collections

from randovania.games.yokus_island_express.exporter.patch_data_factory import YokuPatchDataFactory
from randovania.games.yokus_island_express.layout import YokuCosmeticPatches
from randovania.interface_common.worlds_configuration import WorldsConfiguration
from randovania.layout.layout_description import LayoutDescription

TRACKERS = {"tracker_caves", "tracker_jungle", "tracker_peak", "tracker_scarabs", "tracker_springs"}


def _create_data(test_files_dir, mocker, rdvgame: str) -> tuple[YokuPatchDataFactory, dict]:
    mocker.patch("randovania.exporter.patch_data_factory.PatchDataFactory._attach_to_sentry")
    description = LayoutDescription.from_file(
        test_files_dir.joinpath("log_files", "yokus_island_express", f"{rdvgame}.rdvgame")
    )
    factory = YokuPatchDataFactory(
        description,
        WorldsConfiguration(world_index=0, world_names={0: "World 1"}),
        YokuCosmeticPatches(),
    )
    data = factory.create_data()
    data.pop("_randovania_meta")
    return factory, data


def test_create_data_starting_trackers(test_files_dir, mocker) -> None:
    _, data = _create_data(test_files_dir, mocker, "starter_preset")
    items = collections.Counter(pickup["item"] for pickup in data["pickups"])

    assert data["starting_items"] == dict.fromkeys(sorted(TRACKERS), 1)
    assert not TRACKERS & set(items)
    # The 5 locations freed by the starting trackers hold Nothing
    assert items["reward_fruit_medium"] == 39
    assert items["nothing"] == 5
    assert data["starting_fruit"] == 0


def test_create_data_shuffled_trackers(test_files_dir, mocker) -> None:
    _, data = _create_data(test_files_dir, mocker, "shuffled_trackers")
    items = collections.Counter(pickup["item"] for pickup in data["pickups"])

    assert data["starting_items"] == {}
    assert all(items[tracker] == 1 for tracker in TRACKERS)
    assert items["reward_fruit_medium"] == 39


def test_create_data_starting_fruit(test_files_dir, mocker) -> None:
    _, data = _create_data(test_files_dir, mocker, "starting_fruit")

    assert data["starting_fruit"] == 50
