import argparse
import collections
import json
from pathlib import Path
from statistics import stdev
from typing import Dict


def read_json(path: Path) -> dict:
    with path.open() as x:
        return json.load(x)


def accumulate_results(layout: dict, items: dict, locations: dict):
    for worlds, world_data in layout["game_modifications"]["locations"].items():
        for area_name, item_name in world_data.items():
            items[item_name][area_name] += 1
            locations[area_name][item_name] += 1


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


def create_report(seeds_dir: str, output_file: str):
    def item_creator():
        return collections.defaultdict(int)

    items = collections.defaultdict(item_creator)
    locations = collections.defaultdict(item_creator)

    seed_count = 0
    pickup_count = None
    for seed in Path(seeds_dir).glob("**/*.json"):
        accumulate_results(read_json(seed), items, locations)
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
