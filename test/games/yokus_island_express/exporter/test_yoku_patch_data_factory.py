from __future__ import annotations

import collections

from randovania.games.yokus_island_express.exporter.patch_data_factory import YokuPatchDataFactory
from randovania.games.yokus_island_express.layout import YokuCosmeticPatches
from randovania.interface_common.worlds_configuration import WorldsConfiguration
from randovania.layout.layout_description import LayoutDescription

TRACKERS = {"tracker_caves", "tracker_jungle", "tracker_peak", "tracker_scarabs", "tracker_springs"}


def _create_data(test_files_dir, mocker, rdvgame: str, world_index: int = 0) -> tuple[YokuPatchDataFactory, dict]:
    mocker.patch("randovania.exporter.patch_data_factory.PatchDataFactory._attach_to_sentry")
    description = LayoutDescription.from_file(test_files_dir.joinpath("log_files", rdvgame))
    factory = YokuPatchDataFactory(
        description,
        WorldsConfiguration(
            world_index=world_index,
            world_names={i: f"World {i + 1}" for i in range(description.world_count)},
        ),
        YokuCosmeticPatches(),
    )
    data = factory.create_data()
    data.pop("_randovania_meta")
    return factory, data


def test_create_data_starting_trackers(test_files_dir, mocker) -> None:
    _, data = _create_data(test_files_dir, mocker, "yokus_island_express/starter_preset.rdvgame")
    items = collections.Counter(pickup["item"] for pickup in data["pickups"])

    assert data["starting_items"] == dict.fromkeys(sorted(TRACKERS), 1)
    assert not TRACKERS & set(items)
    # The 5 locations freed by the starting trackers hold Nothing
    assert items["reward_fruit_medium"] == 39
    assert items["nothing"] == 5
    assert data["starting_fruit"] == 0
    assert data["required_beacons"] == 0


def test_create_data_shuffled_trackers_fruit_beacons(test_files_dir, mocker) -> None:
    _, data = _create_data(test_files_dir, mocker, "yokus_island_express/shuffled_trackers_fruit_beacons.rdvgame")
    items = collections.Counter(pickup["item"] for pickup in data["pickups"])

    assert data["starting_items"] == {}
    assert all(items[tracker] == 1 for tracker in TRACKERS)
    assert items["reward_fruit_medium"] == 39
    assert data["starting_fruit"] == 50
    assert data["required_beacons"] == 2


def test_create_data_seed_hash(test_files_dir, mocker) -> None:
    factory, data = _create_data(test_files_dir, mocker, "yokus_island_express/starter_preset.rdvgame")
    description = factory.description

    # The game's menu shows the hash the way Randovania does.
    assert data["seed_hash"] == f"{description.shareable_word_hash} ({description.shareable_hash})"
    assert data["configuration_identifier"] == description.shareable_hash


def test_create_data_multiworld(test_files_dir, mocker) -> None:
    factory, data = _create_data(test_files_dir, mocker, "multi-dread+msr+yoku.rdvgame", world_index=2)
    region_list = factory.game.region_list
    pickups = {pickup["location"]: pickup for pickup in data["pickups"]}
    other_worlds = set()

    for index, target in factory.patches.pickup_assignment.items():
        pickup = pickups[region_list.node_from_pickup_index(index).extra["spawn_id"]]
        if target.world == 2:
            assert "caption" not in pickup
        else:
            other_worlds.add(target.world)
            assert pickup == {
                "location": pickup["location"],
                "item": "nothing",
                "caption": f"Sent {target.pickup.name} to World {target.world + 1}!",
            }

    assert other_worlds == {0, 1}
