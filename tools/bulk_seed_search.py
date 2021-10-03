import argparse
import collections
import json
import re
import typing
from pathlib import Path

from randovania.layout.layout_description import LayoutDescription


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
_PLAYER_MATCH = re.compile(r" for Player \d+")


def _filter_item_name(name: str) -> str:
    return _PLAYER_MATCH.sub("", _KEY_MATCH.sub("Key", name))


def create_report(seeds_dir: str, output_file: str):
    def item_creator():
        return collections.defaultdict(list)

    item_name_to_location = collections.defaultdict(item_creator)

    seed_files = list(Path(seeds_dir).glob(f"**/*.{LayoutDescription.file_extension()}"))
    seed_files.extend(Path(seeds_dir).glob("**/*.json"))
    for seed in iterate_with_log(seed_files):
        seed = typing.cast(Path, seed)
        try:
            seed_data = read_json(seed)
        except json.JSONDecodeError:
            continue

        for item_order in seed_data["item_order"]:
            if " as " in item_order:
                continue

            item_name, item_location = item_order.split(" at ", 1)
            item_name = _filter_item_name(item_name)
            item_location = item_location.split(" with hint ", 1)[0]

            if "Expansion" in item_name or item_name == "Energy Tank":
                continue

            item_name_to_location[item_name][item_location].append(str(seed.relative_to(seeds_dir)))

    final_results = {
        item_name: {
            location: seeds
            for location, seeds in sorted(locations.items(), key=lambda it: len(it[1]))
            if len(seeds) < 250
        }
        for item_name, locations in sorted(item_name_to_location.items(), key=lambda it: it[0])
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
