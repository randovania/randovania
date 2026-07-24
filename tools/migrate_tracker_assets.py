"""
One-off migration script for the item tracker refactor.

Splits each combined tracker JSON under randovania/data/gui_assets/tracker/ into a
"structure" file (logic: position, resources, thresholds) and a "theme" file (visuals: image
paths, label text/style), rewriting trackers.json to point each display name at a
structure/theme pair instead of a single flat file. Structurally identical files (e.g.
`prime1-game.json` vs `prime1-pixel.json`, which only differ in images) are deduplicated onto
a single structure file.

Run once via `uv run python tools/migrate_tracker_assets.py`, review the output, then delete
the old flat per-game JSON files that `trackers.json` used to reference (image asset folders
like `game-images/` and `pixel-icons/` are untouched).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from randovania.lib import json_lib

DEFAULT_TRACKER_DIR = Path(__file__).parent.parent / "randovania" / "data" / "gui_assets" / "tracker"

_STRUCTURE_KEYS_TO_DROP = ("image_path", "disabled_image_path", "label", "style")


def _kind_of(element: dict[str, Any]) -> str:
    if "image_path" in element:
        return "image"
    if "progress_bar" in element:
        return "progress_bar"
    if "label" in element:
        return "label"
    raise ValueError(f"Cannot determine kind of element: {element}")


def _split_element(element: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    kind = _kind_of(element)
    structure = {k: v for k, v in element.items() if k not in _STRUCTURE_KEYS_TO_DROP}
    structure["kind"] = kind

    theme: dict[str, Any] = {}
    if kind == "image":
        theme["image_path"] = element["image_path"]
        if "disabled_image_path" in element:
            theme["disabled_image_path"] = element["disabled_image_path"]
    elif kind == "label":
        theme["text"] = element["label"]
        if "style" in element:
            theme["style"] = element["style"]
    # progress_bar elements have nothing themable today

    return structure, theme


def _fingerprint(game: str, structure_elements: list[dict[str, Any]], extra: dict[str, Any]) -> str:
    return json.dumps({"game": game, "elements": structure_elements, "extra": extra}, sort_keys=True)


def _slug_from_stem(stem: str) -> str:
    return stem.replace("-pixel", "").replace("-game", "")


def migrate(tracker_dir: Path = DEFAULT_TRACKER_DIR) -> None:
    trackers_json = tracker_dir / "trackers.json"
    trackers_config = json_lib.read_dict(trackers_json)
    all_trackers: dict[str, dict[str, str]] = trackers_config["trackers"]  # type: ignore[assignment]

    structures_dir = tracker_dir / "structures"
    themes_dir = tracker_dir / "themes"

    new_trackers: dict[str, dict[str, dict[str, str]]] = {}
    # per game: fingerprint -> slug, and slug -> fingerprint (to catch accidental slug collisions)
    fingerprint_to_slug: dict[str, dict[str, str]] = {}
    slug_to_fingerprint: dict[str, dict[str, str]] = {}

    files_read = 0
    structures_written = 0
    themes_written = 0

    for game, entries in all_trackers.items():
        new_trackers[game] = {}
        fingerprint_to_slug.setdefault(game, {})
        slug_to_fingerprint.setdefault(game, {})

        for display_name, filename in entries.items():
            source_path = tracker_dir / filename
            raw = json_lib.read_dict(source_path)
            files_read += 1

            elements: list[dict[str, Any]] = raw["elements"]  # type: ignore[assignment]
            extra: dict[str, Any] = raw.get("extra", {})  # type: ignore[assignment]

            structure_elements: list[dict[str, Any]] = []
            theme_images: dict[str, dict[str, Any]] = {}
            theme_labels: dict[str, dict[str, Any]] = {}
            for index, element in enumerate(elements):
                structure_element, theme_element = _split_element(element)
                structure_elements.append(structure_element)

                kind = structure_element["kind"]
                if kind == "image":
                    theme_images[str(index)] = theme_element
                elif kind == "label":
                    theme_labels[str(index)] = theme_element

            fingerprint = _fingerprint(str(raw["game"]), structure_elements, extra)
            slug = fingerprint_to_slug[game].get(fingerprint)
            if slug is None:
                slug = _slug_from_stem(Path(filename).stem)
                if slug in slug_to_fingerprint[game] and slug_to_fingerprint[game][slug] != fingerprint:
                    raise ValueError(
                        f"Slug collision for game {game!r}: {slug!r} derived from {filename!r} "
                        f"already maps to a different structure"
                    )
                fingerprint_to_slug[game][fingerprint] = slug
                slug_to_fingerprint[game][slug] = fingerprint

                json_lib.write_path(
                    structures_dir / f"{slug}.json",
                    {"game": raw["game"], "elements": structure_elements, "extra": extra},
                )
                structures_written += 1

            theme_stem = Path(filename).stem
            json_lib.write_path(
                themes_dir / f"{theme_stem}.json",
                {"images": theme_images, "labels": theme_labels},
            )
            themes_written += 1

            new_trackers[game][display_name] = {
                "structure": f"structures/{slug}.json",
                "theme": f"themes/{theme_stem}.json",
            }

    trackers_config["trackers"] = new_trackers
    json_lib.write_path(trackers_json, trackers_config)

    print(f"Files read: {files_read}")
    print(f"Structure files written: {structures_written}")
    print(f"Theme files written: {themes_written}")


if __name__ == "__main__":
    migrate(Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_TRACKER_DIR)
