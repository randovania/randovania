from __future__ import annotations

import typing
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from randovania.game.game_enum import RandovaniaGame
from randovania.lib import json_lib


def _game_tracker_dirs() -> Iterator[tuple[RandovaniaGame, Path]]:
    for game in RandovaniaGame.all_games():
        game_dir = game.data_path.joinpath("assets", "tracker")
        if game_dir.joinpath("trackers.json").is_file():
            yield game, game_dir


@pytest.mark.parametrize(("game", "game_dir"), list(_game_tracker_dirs()), ids=lambda v: getattr(v, "value", v))
def test_layouts_only_reference_declared_image_names(game: RandovaniaGame, game_dir: Path):
    trackers_config = typing.cast("dict[str, Any]", json_lib.read_dict(game_dir / "trackers.json"))
    declared_images: set[str] = set(trackers_config["images"])

    for layout_name, filename in trackers_config["layouts"].items():
        structure = typing.cast("dict[str, Any]", json_lib.read_dict(game_dir / filename))
        unlisted = {
            element["name"]
            for element in structure["elements"]
            if element["kind"] == "image" and element["name"] not in declared_images
        }
        assert not unlisted, f"{game.value}/{layout_name} references undeclared image names: {unlisted}"


@pytest.mark.parametrize(("game", "game_dir"), list(_game_tracker_dirs()), ids=lambda v: getattr(v, "value", v))
def test_themes_cover_every_declared_image_name(game: RandovaniaGame, game_dir: Path):
    trackers_config = typing.cast("dict[str, Any]", json_lib.read_dict(game_dir / "trackers.json"))
    declared_images: set[str] = set(trackers_config["images"])

    for theme_name, filename in trackers_config["themes"].items():
        theme = typing.cast("dict[str, Any]", json_lib.read_dict(game_dir / filename))
        missing = declared_images - theme["images"].keys()
        assert not missing, f"{game.value}/{theme_name} is missing images for: {missing}"
