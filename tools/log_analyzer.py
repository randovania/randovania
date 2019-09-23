import argparse
import collections
import copy
import csv
import json
import os
from pathlib import Path
from statistics import stdev
from typing import Dict, Tuple, Optional

from randovania.game_description.default_database import default_prime2_game_description
from randovania.game_description.node import PickupNode, LogbookNode


def read_json(path: Path) -> dict:
    with path.open() as x:
        return json.load(x)


def accumulate_results(layout: dict,
                       items: Dict[str, Dict[str, int]],
                       locations: Dict[str, Dict[str, int]],
                       item_hints: Dict[str, Dict[str, int]],
                       location_hints: Dict[str, Dict[str, int]],

                       index_to_location: Dict[int, Tuple[str, str]],
                       logbook_to_name: Dict[str, str],
                       ):
    for worlds, world_data in layout["game_modifications"]["locations"].items():
        for area_name, item_name in world_data.items():
            items[item_name][area_name] += 1
            locations[area_name][item_name] += 1

    for logbook_asset, hint_data in layout["game_modifications"]["hints"].items():
        if hint_data["hint_type"] != "location":
            continue

        logbook_asset = logbook_to_name[logbook_asset]

        if hint_data["target"] == -1:
            item_name = "Nothing"
        else:
            area_name, location_name = index_to_location[hint_data["target"]]
            item_name = layout["game_modifications"]["locations"][area_name][location_name]

        location_hints[logbook_asset][item_name] += 1
        item_hints[item_name][logbook_asset] += 1


def calculate_pickup_count(items: Dict[str, Dict[str, int]]) -> Dict[str, int]:
    return {
        name: sum(data.values())
        for name, data in items.items()
    }


def sort_by_contents(data: dict) -> dict:
    return {
        item: {
            location: count
            for location, count in sorted(data[item].items(), key=lambda t: t[1], reverse=True)
        }
        for item in sorted(data.keys())
    }


def calculate_stddev(pickup_count: Dict[str, int], item_counts: Dict[str, float]) -> float:
    balanced_freq = {
        item: count / pickup_count[item]
        for item, count in item_counts.items()
    }
    return stdev(balanced_freq.values())


def first_key(d: dict):
    for key in d:
        return key


def create_report(seeds_dir: str, output_file: str, csv_dir: Optional[str]):
    def item_creator():
        return collections.defaultdict(int)

    items = collections.defaultdict(item_creator)
    locations = collections.defaultdict(item_creator)
    item_hints = collections.defaultdict(item_creator)
    location_hints = collections.defaultdict(item_creator)

    game_description = default_prime2_game_description()
    index_to_location = {
        node.pickup_index.index: (game_description.world_list.nodes_to_world(node).name,
                                  game_description.world_list.node_name(node))
        for node in game_description.world_list.all_nodes
        if isinstance(node, PickupNode)
    }

    logbook_to_name = {
        str(node.string_asset_id): game_description.world_list.node_name(node)
        for node in game_description.world_list.all_nodes
        if isinstance(node, LogbookNode)
    }

    seed_count = 0
    pickup_count = None
    for seed in Path(seeds_dir).glob("**/*.json"):
        accumulate_results(read_json(seed),
                           items, locations,
                           item_hints, location_hints,
                           index_to_location, logbook_to_name)
        if seed_count == 0:
            pickup_count = calculate_pickup_count(items)
        seed_count += 1

    if pickup_count is None:
        raise Exception("No seeds found")

    stddev_by_location = {
        location: calculate_stddev(pickup_count, locations[location])
        for location in locations.keys()
    }

    final_results = {
        "seed_count": seed_count,
        "stddev_by_location": {
            location: stddev
            for location, stddev in sorted(stddev_by_location.items(), key=lambda t: t[1], reverse=True)
        },
        "items": sort_by_contents(items),
        "locations": sort_by_contents(locations),
        "item_hints": sort_by_contents(item_hints),
        "location_hints": sort_by_contents(location_hints),
    }

    if csv_dir is not None:
        os.makedirs(csv_dir, exist_ok=True)
        for field in "items", "locations", "item_hints", "location_hints":
            data = final_results[field]

            possible_columns = set()
            for potential_values in data.values():
                possible_columns |= set(potential_values.keys())

            possible_columns = list(sorted(possible_columns))
            possible_columns.insert(0, "row_name")

            with open(os.path.join(csv_dir, field + ".csv"), "w", newline='') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=possible_columns)
                writer.writeheader()

                for column, row_data in data.items():
                    row_data = copy.copy(row_data)
                    row_data["row_name"] = column
                    writer.writerow(row_data)

    with open(output_file, "w") as output:
        json.dump(final_results, output, indent=4, separators=(',', ': '))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv-dir")
    parser.add_argument("seeds_dir")
    parser.add_argument("output_file")
    args = parser.parse_args()
    create_report(args.seeds_dir, args.output_file,
                  args.csv_dir)


if __name__ == "__main__":
    main()
