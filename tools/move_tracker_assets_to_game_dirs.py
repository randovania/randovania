"""
Fourth one-off migration for the item tracker refactor.

Moves each game's tracker directory out of the shared randovania/data/gui_assets/tracker/
into that game's own assets folder (randovania/games/<game>/assets/tracker/), matching the
existing convention for other per-game assets (maps/, icon/, suit_renders/, ...) and the
existing PyInstaller packaging rule that already bundles randovania/games/<game>/assets/**.

Rewrites every theme file's image_path/disabled_image_path strings to drop the now-obsolete
"gui_assets/tracker/<game>/" prefix, since they're resolved relative to the game's own tracker
directory from now on (see TrackerAssetPaths.assets_root).

Run once via `uv run python tools/move_tracker_assets_to_game_dirs.py [source_dir] [games_dir]`,
defaulting to the repo's randovania/data/gui_assets/tracker and randovania/games.

For a directory that's already organized per-game but just needs its embedded image paths
fixed up (e.g. a local persistence override, which lives directly under
<user>/tracker/layout/<game>/ with no move to make), pass the same path for both arguments -
this only rewrites paths in place and skips moving anything.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from randovania.lib import json_lib

DEFAULT_SOURCE_DIR = Path(__file__).parent.parent / "randovania" / "data" / "gui_assets" / "tracker"
DEFAULT_GAMES_DIR = Path(__file__).parent.parent / "randovania" / "games"


def _rewrite_image_paths(theme: dict[str, Any], old_prefix: str) -> None:
    def fix(value: Any) -> Any:
        if isinstance(value, str) and value.startswith(old_prefix):
            return value[len(old_prefix) :]
        if isinstance(value, list):
            return [fix(v) for v in value]
        return value

    for entry in theme.get("images", {}).values():
        for key in ("image_path", "disabled_image_path"):
            if key in entry:
                entry[key] = fix(entry[key])


def migrate(source_dir: Path, games_dir: Path) -> None:
    move = source_dir != games_dir
    processed = 0

    for game_dir in sorted(source_dir.iterdir()):
        if not game_dir.is_dir():
            continue

        game = game_dir.name
        old_prefix = f"gui_assets/tracker/{game}/"

        for theme_path in game_dir.joinpath("themes").glob("*.json"):
            theme = json_lib.read_dict(theme_path)
            _rewrite_image_paths(theme, old_prefix)
            json_lib.write_path(theme_path, theme)

        if move:
            dest_dir = games_dir / game / "assets" / "tracker"
            dest_dir.parent.mkdir(parents=True, exist_ok=True)
            game_dir.rename(dest_dir)

        processed += 1

    if move and not any(source_dir.iterdir()):
        source_dir.rmdir()

    print(f"Games processed: {processed}")


if __name__ == "__main__":
    args = sys.argv[1:]
    source = Path(args[0]) if len(args) > 0 else DEFAULT_SOURCE_DIR
    games = Path(args[1]) if len(args) > 1 else DEFAULT_GAMES_DIR
    migrate(source, games)
