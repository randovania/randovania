from __future__ import annotations

import struct

import pytest

from randovania.game.game_enum import RandovaniaGame
from randovania.game_description import default_database
from randovania.game_description.db.event_node import EventNode
from randovania.game_description.db.pickup_node import PickupNode
from randovania.game_description.pickup.pickup_entry import StartingPickupBehavior
from randovania.game_description.requirements.resource_requirement import ResourceRequirement

GAME = RandovaniaGame.YOKUS_ISLAND_EXPRESS


@pytest.fixture(scope="module")
def yoku_game_description():
    return default_database.game_description_for(GAME)


def _pickup_nodes(game) -> list[PickupNode]:
    nodes = [node for node in game.region_list.all_nodes if isinstance(node, PickupNode)]
    return sorted(nodes, key=lambda node: node.pickup_index)


def test_pickup_pool_fills_every_location(yoku_game_description) -> None:
    pickup_database = default_database.pickup_database_for_game(GAME)
    standard_pickups = pickup_database.standard_pickups.values()

    assert sum(pickup.count_for_shuffled_case for pickup in standard_pickups) == len(
        _pickup_nodes(yoku_game_description)
    )
    for pickup in standard_pickups:
        is_fruit = pickup.extra["item_id"].startswith("reward_fruit")
        assert (pickup.starting_condition == StartingPickupBehavior.CAN_NEVER_BE_STARTING) == is_fruit


def _webp_size(path) -> tuple[int, int]:
    """Width and height of a lossy WebP: the VP8 frame header, after the RIFF and chunk headers."""
    header = path.read_bytes()[:30]
    assert header[:4] == b"RIFF", path.name
    assert header[8:12] == b"WEBP", path.name
    assert header[12:16] == b"VP8 ", f"{path.name} is not a lossy WebP"
    assert header[23:26] == bytes((0x9D, 0x01, 0x2A)), f"{path.name} has no VP8 keyframe sync code"
    width, height = struct.unpack("<HH", header[26:30])
    return width & 0x3FFF, height & 0x3FFF


def test_region_map_pictures_cover_the_areas(yoku_game_description) -> None:
    for region in yoku_game_description.region_list.regions:
        width, height = _webp_size(GAME.data_path.joinpath("assets", "maps", f"{region.name}.webp"))

        boundings = [area.extra["total_boundings"] for area in region.areas]
        region_width = max(b["x2"] for b in boundings) - min(b["x1"] for b in boundings)
        region_height = max(b["y2"] for b in boundings) - min(b["y1"] for b in boundings)
        assert width / height == pytest.approx(region_width / region_height, rel=0.002), region.name


def test_start_location(yoku_game_description) -> None:
    assert yoku_game_description.starting_location.as_string == "Intro/Landing/Beach"


def _event_node(game, event: str) -> EventNode:
    (node,) = [
        node for node in game.region_list.all_nodes if isinstance(node, EventNode) and node.event.short_name == event
    ]
    return node


def test_victory(yoku_game_description) -> None:
    victory_node = _event_node(yoku_game_description, "Victory")

    assert victory_node.identifier.area_identifier.as_tuple == ("Hub", "Mokumas Pit")
    assert yoku_game_description.victory_condition == ResourceRequirement.simple(victory_node.event)


def test_sootling_leash_only_unlocks_the_grapple_event(yoku_game_description) -> None:
    """The leash is redeemed at the Frostpine Forest sootling, whose event grants the Hook item."""
    game = yoku_game_description
    leashed = _event_node(game, "SootlingFound")
    assert leashed.identifier.area_identifier.as_tuple == ("Peak", "Frostpine Forest")

    needing_the_leash = []
    for area in game.region_list.all_areas:
        for targets in area.connections.values():
            for target, requirement in targets.items():
                resources = {
                    req.resource.short_name for req in requirement.iterate_resource_requirements(game.resource_database)
                }
                if "SootlingLeash" in resources:
                    needing_the_leash.append(target)
    assert needing_the_leash == [leashed]
