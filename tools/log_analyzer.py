import argparse
import collections
import json
from statistics import stdev
from typing import Dict, List

import py

from randovania.game_description.resources import PickupEntry
from randovania.interface_common.echoes import default_prime2_pickup_database


def read_json(path: str) -> dict:
    with open(path) as x:
        return json.load(x)


def accumulate_results(layout: dict, items: dict, locations: dict):
    for worlds, world_data in layout["locations"].items():
        for area_name, item_name in world_data.items():
            items[item_name][area_name] += 1
            locations[area_name][item_name] += 1


def sort_by_contents(data: dict) -> dict:
    return {
        item: {
            location: count
            for location, count in sorted(data[item].items(), key=lambda t: t[1], reverse=True)
        }
        for item in sorted(data.keys())
    }


def calculate_stddev(split_pickups: Dict[str, List[PickupEntry]], item_counts: Dict[str, float]) -> float:
    balanced_freq = {
        item: count / len(split_pickups[item])
        for item, count in item_counts.items()
    }
    return stdev(balanced_freq.values())


def create_report(seeds_dir: str, output_file: str):
    def item_creator():
        return collections.defaultdict(int)

    items = collections.defaultdict(item_creator)
    locations = collections.defaultdict(item_creator)

    seed_count = 0
    for seed in py.path.local(seeds_dir).visit("*.json"):
        accumulate_results(read_json(seed), items, locations)
        seed_count += 1

    pickup_database = default_prime2_pickup_database()
    split_pickups = pickup_database.pickups_split_by_name()

    stddev_by_location = {
        location: calculate_stddev(split_pickups, locations[location])
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
    }

    with open(output_file, "w") as output:
        json.dump(final_results, output, indent=4, separators=(',', ': '))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("seeds_dir")
    parser.add_argument("output_file")
    args = parser.parse_args()
    create_report(args.seeds_dir, args.output_file)


if __name__ == "__main__":
    main()
