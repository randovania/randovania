import argparse
import collections
import copy
import csv
import json
import math
import os
import re
import statistics
from pathlib import Path
from statistics import stdev
from typing import Dict, Tuple, Optional, List, Iterable, Set

from randovania.layout.layout_description import LayoutDescription

NON_MAJOR_PROGRESSION = [
    "Missile Expansion",
    "Energy Tank",
    "Energy Transfer Module",
    "Artifact",
    "Power Bomb Expansion",
    "Ice Spreader",
    "Wavebuster",
    "Gravity Suit",
    "Flamethrower",
    "X-Ray Visor",
    "Grapple Beam",
    "Thermal Visor",
    "Phazon Suit",
    "Sonic Boom",
    "Darkburst",
    "Sunburst",
    "Unlimited Missiles",
    "Unlimited Beam Ammo",
    "Double Damage",
    "Cannon Ball",
    "Dark Ammo Expansion",
    "Light Ammo Expansion",
    "Beam Ammo Expansion",
]


def is_non_major_progression(x: str):
    x = x.lower()
    for item in NON_MAJOR_PROGRESSION:
        if x == item.lower():
            return True
    return False


def iterate_with_log(x):
    try:
        import tqdm
        return tqdm.tqdm(x)
    except ImportError:
        print("WARNING: tqdm not found. Use `pip install tqdm` to have progress feedback.")
        return x


def read_json(path: Path) -> dict:
    with path.open() as x:
        return json.load(x)


_KEY_MATCH = re.compile(r"Key (\d+)")
_ARTIFACT_MATCH = re.compile(r"Artifact of (\w+)")
_DNA_MATCH = re.compile(r"Metroid DNA (\d+)")
_PLAYER_MATCH = re.compile(r" for Player \d+")
_FILTERING = [
    (_KEY_MATCH, "Key"),
    (_ARTIFACT_MATCH, "Artifact"),
    (_DNA_MATCH, "Metroid DNA"),
    (_PLAYER_MATCH, ""),
]


def _filter_item_name(name: str) -> str:
    result = name
    for match, sub in _FILTERING:
        result = match.sub(sub, result)
    return result


def accumulate_results(game_modifications: dict,
                       items: Dict[str, Dict[str, int]],
                       locations: Dict[str, Dict[str, int]],
                       major_progression_items_only: bool,
                       ):
    for world_name, world_data in game_modifications["locations"].items():
        for area_name, item_name in world_data.items():
            area_name = f"{world_name}/{area_name}"
            item_name = _filter_item_name(item_name)
            if major_progression_items_only and is_non_major_progression(item_name):
                continue
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


def calculate_stddev(pickup_count: Dict[str, int], item_counts: Dict[str, float]) -> Optional[float]:
    balanced_freq = {
        item: count / pickup_count[item]
        for item, count in item_counts.items()
        if item in pickup_count
    }
    try:
        return stdev(balanced_freq.values())
    except statistics.StatisticsError:
        return None


def first_key(d: dict):
    for key in d:
        return key


def get_items_order(all_items: Iterable[str], item_order: List[str], major_progression_items_only: bool) -> Tuple[
    Dict[str, int], Set[str], Set[str], Set[str]]:
    locations = set()
    no_key = set()
    progression_items = set()
    order = {}

    for i, entry in enumerate(item_order):
        splitter = " as "
        if splitter not in entry:
            splitter = " at "
        item, location = entry.split(splitter, 1)
        if major_progression_items_only and is_non_major_progression(item):
            continue
        order[item] = i
        location = location.split(" with ", 1)[0]
        locations.add(location)
        if "key" not in item.lower() and "artifact" not in item.lower():
            no_key.add(location)

        progression_items.add(item.split("'s ")[-1])

    for item in all_items:
        if item not in order:
            order[item] = len(item_order)

    return order, locations, no_key, progression_items


def create_report(seeds_dir: str, output_file: str, csv_dir: Optional[str], use_percentage: bool,
                  major_progression_items_only: bool):
    def item_creator():
        return collections.defaultdict(int)

    items = collections.defaultdict(item_creator)
    locations = collections.defaultdict(item_creator)
    item_order = collections.defaultdict(list)

    progression_count_for_location = collections.defaultdict(int)
    progression_no_key_count_for_location = collections.defaultdict(int)

    seed_count = 0
    pickup_count = None
    progression_items = None

    seed_files = list(Path(seeds_dir).glob(f"**/*.{LayoutDescription.file_extension()}"))
    seed_files.extend(Path(seeds_dir).glob("**/*.json"))
    for seed in iterate_with_log(seed_files):
        try:
            seed_data = read_json(seed)
        except json.JSONDecodeError:
            continue

        for game_modifications in seed_data["game_modifications"]:
            accumulate_results(game_modifications, items, locations, major_progression_items_only)
        if seed_count == 0:
            pickup_count = calculate_pickup_count(items)

        item_orders, locations_with_progression, no_key_progression, _progression_items = get_items_order(
            list(items.keys()),
            seed_data["item_order"], major_progression_items_only)
        for item, order in item_orders.items():
            item_order[item].append(order)

        for location in locations_with_progression:
            progression_count_for_location[location] += 1

        for location in no_key_progression:
            progression_no_key_count_for_location[location] += 1

        if progression_items is None:
            progression_items = _progression_items

        seed_count += 1

    if pickup_count is None:
        raise Exception("No seeds found")

    stddev_by_location = {
        location: calculate_stddev(pickup_count, locations[location])
        for location in locations.keys()
    }

    regions = dict()
    region_totals = dict()

    total_progression_item_count = 0
    for location in locations:
        region = location.split("/")[0]

        if region not in regions.keys():
            regions[region] = 0

        if region not in region_totals.keys():
            region_totals[region] = 0
        region_totals[region] += 1

        count = 0
        for item in locations[location]:
            if (item in progression_items) and ("artifact" not in item.lower()) and ("key" not in item.lower()):
                count = count + locations[location][item]
        total_progression_item_count += count
        regions[region] += count

    # probability that any given location in this region contains progression
    regions_weighted = dict()
    for region in regions:
        regions_weighted[region] = (regions[region] / seed_count) / region_totals[region]

    items = sort_by_contents(items)
    locations = sort_by_contents(locations)

    location_progression_count = {
        location: value
        for location, value in sorted(progression_count_for_location.items(), key=lambda t: t[1], reverse=True)
    }

    location_progression_no_key_count = {
        location: value
        for location, value in sorted(progression_no_key_count_for_location.items(),
                                      key=lambda t: t[1], reverse=True)
    }

    stddev_by_location = {
        location: stddev
        for location, stddev in sorted(stddev_by_location.items(), key=lambda t: t[1] or math.inf, reverse=True)
    }

    ## Average standardized deviances for all locations
    accumulated_stddev = 0
    stddev_count = 0
    for stddev in stddev_by_location.items():
        try:
            accumulated_stddev += stddev[1]
            stddev_count += 1
        except:
            pass
    accumulated_stddev /= stddev_count * 2  # div by 2 because +1 deviance at one location always implies +1 everywhere else

    ## Accumulate deviances for all locations

    # 100% unbiased logicless progression probablitity per location
    pure_median = (total_progression_item_count / seed_count) / len(locations)

    # Accumulate deviances
    bias_index = 0
    for location in location_progression_count:
        bias_index += abs(location_progression_count[location] / seed_count - pure_median)

    # Scale and account for the fact that 1% deviance in one location always results for 1% elsewhere
    bias_index /= 2

    for location in locations:
        if location not in location_progression_no_key_count.keys():
            location_progression_no_key_count[location] = 0

        if location not in location_progression_count.keys():
            location_progression_count[location] = 0

        for item in items:
            if location not in items[item].keys():
                items[item][location] = 0

    if use_percentage:
        for item in items:
            for room in items[item]:
                items[item][room] = items[item][room] / seed_count
        for location in locations:
            for item in locations[location]:
                locations[location][item] = locations[location][item] / seed_count
        for location in location_progression_count:
            location_progression_count[location] = location_progression_count[location] / seed_count
        for location in location_progression_no_key_count:
            location_progression_no_key_count[location] = location_progression_no_key_count[location] / seed_count
        for region in regions:
            regions[region] = regions[region] / total_progression_item_count

    final_results = {
        "seed_count": seed_count,
        "accumulated_stddev": accumulated_stddev,
        "bias_index": bias_index,
        "regions": regions,
        "regions_weighted": regions_weighted,
        "stddev_by_location": stddev_by_location,
        "items": items,
        "locations": locations,
        "location_progression_count": location_progression_count,
        "location_progression_no_key_count": location_progression_no_key_count,
        "item_order": {
            "average": {
                name: statistics.mean(orders)
                for name, orders in item_order.items()
            },
            "median": {
                name: int(statistics.median(orders))
                for name, orders in item_order.items()
            },
            "stdev": {
                name: statistics.stdev(orders)
                for name, orders in item_order.items()
            },
        }
    }

    # add non-item insights to csv file
    for location in locations:
        locations[location]["Progression Probability"] = location_progression_no_key_count[location]

    if csv_dir is not None:
        os.makedirs(csv_dir, exist_ok=True)
        for field in "items", "locations", "item_hints", "location_hints", "regions":
            data = final_results[field]

            if field == "regions":
                data = {
                    "Share of Progression": final_results["regions"],
                    "Locations with Progression": final_results["regions_weighted"],
                }

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
    parser.add_argument('--use-percentage', action='store_true')
    parser.add_argument('--major-progression-only', action='store_true')
    args = parser.parse_args()
    create_report(args.seeds_dir, args.output_file,
                  args.csv_dir, args.use_percentage,
                  args.major_progression_only)


if __name__ == "__main__":
    main()
