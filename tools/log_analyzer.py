import argparse
import collections
import json

import py


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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("seeds_dir")
    parser.add_argument("output_file")
    args = parser.parse_args()

    def item_creator():
        return collections.defaultdict(int)

    items = collections.defaultdict(item_creator)
    locations = collections.defaultdict(item_creator)

    seed_count = 0
    for seed in py.path.local(args.seeds_dir).visit("*.json"):
        accumulate_results(read_json(seed), items, locations)
        seed_count += 1

    final_results = {
        "seed_count": seed_count,
        "items": sort_by_contents(items),
        "locations": sort_by_contents(locations),
    }

    with open(args.output_file, "w") as output:
        json.dump(final_results, output, indent=4, separators=(',', ': '))


if __name__ == "__main__":
    main()
