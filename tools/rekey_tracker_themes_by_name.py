"""
Second one-off migration for the item tracker refactor.

Reworks the structure/theme split introduced by migrate_tracker_assets.py so that:
- Every structure element gets a stable "name" (derived from its resources; for the handful of
  elements with no resources of their own - decorative icons paired with a separate counter
  label, or static captions - derived from that element's own image filename/label text instead).
- Themes are keyed by that name instead of by the element's index in the structure. Index-based
  keys meant a theme file was only ever valid for the exact structure it was authored against;
  name-based keys let the *same* item resolve to the same theme entry across every layout that
  contains it.
- Per-layout theme files that represent the same visual style (e.g. prime1's "Game Art" theme,
  previously duplicated once per layout: Standard/8 Lines/3 Lines/2 Lines) are merged into a
  single theme file covering every layout, since a name-keyed theme just needs to contain the
  names a given layout's structure asks for - nothing layout-specific about the file itself.

Run once via `uv run python tools/rekey_tracker_themes_by_name.py [tracker_dir]`, defaulting to
the repo's randovania/data/gui_assets/tracker. Pass a tracker directory argument for any other
tracker directories that need the same treatment (e.g. a local persistence copy).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

from randovania.lib import json_lib

DEFAULT_TRACKER_DIR = Path(__file__).parent.parent / "randovania" / "data" / "gui_assets" / "tracker"


def _humanize_stem(stem: str) -> str:
    words = re.split(r"[_\-]+", stem)
    if stem.islower():
        return " ".join(word.capitalize() for word in words if word)
    return " ".join(word for word in words if word)


def _hinted_name(index: int, element: dict[str, Any], hint_theme: dict[str, Any]) -> str | None:
    """For an element with no resources of its own, borrow a name from whichever raw visual
    content (an image's filename, or a label's own static text) this element's hint theme has
    for it - this is the only stable identity such an element has."""
    if element["kind"] == "image":
        image = hint_theme.get("images", {}).get(str(index))
        if image is None:
            return None
        image_path = image["image_path"]
        if isinstance(image_path, list):
            image_path = image_path[0]
        return _humanize_stem(Path(image_path).stem)

    if element["kind"] == "label":
        label = hint_theme.get("labels", {}).get(str(index))
        if label is None:
            return None
        return label["text"]

    return None


def _assign_names(elements: list[dict[str, Any]], hint_theme: dict[str, Any]) -> list[str]:
    """Returns one name per element, in the same order as `elements`."""
    raw_names: dict[int, str] = {}
    for i, element in enumerate(elements):
        resources = element.get("resources", [])
        if resources:
            raw_names[i] = " + ".join(resources)
        else:
            hinted = _hinted_name(i, element, hint_theme)
            if hinted is not None:
                raw_names[i] = hinted

    for i, element in enumerate(elements):
        if i not in raw_names:
            raw_names[i] = f"Unnamed ({element['row']},{element['column']})"

    seen_by_kind: dict[str, set[str]] = {"image": set(), "label": set(), "progress_bar": set()}
    result: list[str] = []
    for i, element in enumerate(elements):
        kind = element["kind"]
        name = raw_names[i]
        if name in seen_by_kind[kind]:
            name = f"{name} ({element['row']},{element['column']})"
        seen_by_kind[kind].add(name)
        result.append(name)
    return result


def _normalize_image(image: dict[str, Any]) -> dict[str, Any]:
    """Collapses a single-element image_path list to a plain string.

    Some of the original source files stored a single image as a length-1 list rather than a
    bare string; both mean the same thing to TrackerTheme, but they'd otherwise look like a
    genuine conflict when merging the same item's entry from two different layouts.
    """
    image_path = image.get("image_path")
    if isinstance(image_path, list) and len(image_path) == 1:
        image = {**image, "image_path": image_path[0]}
    return image


def _rekey_theme(path: Path, names: list[str]) -> dict[str, dict[str, Any]]:
    """Reads an index-keyed theme file and returns its content rekeyed by name."""
    raw = json_lib.read_dict(path)
    images: dict[str, Any] = raw.get("images", {})  # type: ignore[assignment]
    labels: dict[str, Any] = raw.get("labels", {})  # type: ignore[assignment]

    return {
        "images": {names[int(index)]: _normalize_image(value) for index, value in images.items()},
        "labels": {names[int(index)]: value for index, value in labels.items()},
    }


def _merge_theme_content(into: dict[str, dict[str, Any]], other: dict[str, dict[str, Any]], context: str) -> None:
    for section in ("images", "labels"):
        for name, value in other[section].items():
            existing = into[section].get(name)
            if existing is not None and existing != value:
                raise ValueError(f"Conflicting {section[:-1]} theme entry for {name!r} while merging {context}")
            into[section][name] = value


def migrate(tracker_dir: Path = DEFAULT_TRACKER_DIR) -> None:
    trackers_json = tracker_dir / "trackers.json"
    trackers_config = json_lib.read_dict(trackers_json)
    all_trackers: dict[str, dict[str, Any]] = trackers_config["trackers"]  # type: ignore[assignment]

    names_by_layout_filename: dict[str, list[str]] = {}

    def names_for(layout_filename: str, hint_theme_filename: str) -> list[str]:
        if layout_filename not in names_by_layout_filename:
            structure_path = tracker_dir / layout_filename
            raw = json_lib.read_dict(structure_path)
            elements: list[dict[str, Any]] = raw["elements"]  # type: ignore[assignment]
            hint_theme = json_lib.read_dict(tracker_dir / hint_theme_filename)

            names = _assign_names(elements, hint_theme)
            for element, name in zip(elements, names):
                element.pop("progress_bar", None)  # stray leftover from the original flat file format
                element["name"] = name
            json_lib.write_path(structure_path, raw)

            names_by_layout_filename[layout_filename] = names
        return names_by_layout_filename[layout_filename]

    new_themes_by_game: dict[str, dict[str, str]] = {}

    for game, game_config in all_trackers.items():
        layouts: dict[str, str] = game_config["layouts"]
        themes: dict[str, dict[str, str]] = game_config["themes"]
        new_themes_by_game[game] = {}

        for theme_name, per_layout in themes.items():
            merged: dict[str, dict[str, Any]] = {"images": {}, "labels": {}}
            theme_paths_used: list[str] = []

            for layout_name, theme_filename in per_layout.items():
                layout_filename = layouts[layout_name]
                names = names_for(layout_filename, theme_filename)
                content = _rekey_theme(tracker_dir / theme_filename, names)
                _merge_theme_content(merged, content, context=f"{game}/{theme_name}/{layout_name}")
                theme_paths_used.append(theme_filename)

            # Reuse the first theme file's name/location for the merged result, and remove the
            # others now that their content lives in the merged file.
            merged_filename = theme_paths_used[0]
            for filename in theme_paths_used[1:]:
                (tracker_dir / filename).unlink()

            json_lib.write_path(tracker_dir / merged_filename, merged)
            new_themes_by_game[game][theme_name] = merged_filename

    for game, game_config in all_trackers.items():
        game_config["themes"] = new_themes_by_game[game]

    json_lib.write_path(trackers_json, trackers_config)

    print(f"Structures rekeyed: {len(names_by_layout_filename)}")
    print(f"Games processed: {len(all_trackers)}")


if __name__ == "__main__":
    migrate(Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_TRACKER_DIR)
