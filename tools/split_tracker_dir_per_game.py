"""
Third one-off migration for the item tracker refactor.

Reorganizes randovania/data/gui_assets/tracker/ from one flat directory shared by every game
into one self-contained directory per game - its own trackers.json, structures/, themes/, and
image asset folders all live together under gui_assets/tracker/<game>/, instead of being
interleaved with every other game's files.

Run once via `uv run python tools/split_tracker_dir_per_game.py [tracker_dir]`, defaulting to
the repo's randovania/data/gui_assets/tracker. Pass a tracker directory argument for any other
tracker directories that need the same treatment (e.g. a local persistence copy).
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path
from typing import Any

from randovania.lib import json_lib

DEFAULT_TRACKER_DIR = Path(__file__).parent.parent / "randovania" / "data" / "gui_assets" / "tracker"

# Physical asset subfolder name(s) for each game - these don't all match the game's own
# RandovaniaGame value (prime1/prime2 use their in-repo short codes, mp1/mp2).
ASSET_SUBFOLDERS = {
    "am2r": ["am2r"],
    "prime1": ["mp1"],
    "prime2": ["mp2"],
    "dread": ["dread"],
    "blank": ["blank"],
    "cave_story": ["cave_story"],
    "samus_returns": ["samus_returns"],
}


def _rewrite_image_paths(obj: Any, game: str) -> None:
    """Prepends "<game>/" to every "gui_assets/tracker/..." path in a theme's raw JSON."""
    prefix = "gui_assets/tracker/"
    new_prefix = f"gui_assets/tracker/{game}/"

    def fix(value: Any) -> Any:
        if isinstance(value, str) and value.startswith(prefix):
            return new_prefix + value[len(prefix) :]
        if isinstance(value, list):
            return [fix(v) for v in value]
        return value

    for section in ("images",):
        for entry in obj.get(section, {}).values():
            for key in ("image_path", "disabled_image_path"):
                if key in entry:
                    entry[key] = fix(entry[key])


def migrate(tracker_dir: Path = DEFAULT_TRACKER_DIR) -> None:
    trackers_json = tracker_dir / "trackers.json"
    trackers_config = json_lib.read_dict(trackers_json)
    all_trackers: dict[str, dict[str, Any]] = trackers_config["trackers"]  # type: ignore[assignment]
    solo_only: dict[str, list[str]] = trackers_config.get("solo_only", {})  # type: ignore[assignment]

    for game, game_config in all_trackers.items():
        game_dir = tracker_dir / game
        game_dir.mkdir(exist_ok=True)

        for filename in game_config["layouts"].values():
            (tracker_dir / filename).parent.mkdir(parents=True, exist_ok=True)
            (game_dir / filename).parent.mkdir(parents=True, exist_ok=True)
            shutil.move(tracker_dir / filename, game_dir / filename)

        for filename in game_config["themes"].values():
            theme = json_lib.read_dict(tracker_dir / filename)
            _rewrite_image_paths(theme, game)
            (game_dir / filename).parent.mkdir(parents=True, exist_ok=True)
            json_lib.write_path(game_dir / filename, theme)
            (tracker_dir / filename).unlink()

        for subfolder in ASSET_SUBFOLDERS.get(game, []):
            for asset_kind in ("game-images", "pixel-icons"):
                src = tracker_dir / asset_kind / subfolder
                if src.is_dir():
                    dst = game_dir / asset_kind / subfolder
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(src, dst)

        json_lib.write_path(
            game_dir / "trackers.json",
            {
                "layouts": game_config["layouts"],
                "themes": game_config["themes"],
                "solo_only": solo_only.get(game, []),
            },
        )

    trackers_json.unlink()
    for leftover in ("structures", "themes", "game-images", "pixel-icons"):
        path = tracker_dir / leftover
        if path.is_dir() and not any(path.rglob("*")):
            shutil.rmtree(path)

    print(f"Games split into their own directory: {len(all_trackers)}")


if __name__ == "__main__":
    migrate(Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_TRACKER_DIR)
