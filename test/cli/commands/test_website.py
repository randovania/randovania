from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from randovania import get_readme_section
from randovania.cli.commands import website


@pytest.mark.parametrize("as_frontmatter", [False, True])
def test_export_videos(tmp_path, as_frontmatter: bool):
    # Setup
    args = MagicMock()
    args.game = None
    args.output_dir = tmp_path
    args.as_frontmatter = as_frontmatter

    # Run
    website.export_videos_yaml_command_logic(args)

    # Check
    fmt = "md" if as_frontmatter else "yml"
    prime1_sz = tmp_path.joinpath(f"prime1.{fmt}").stat().st_size
    assert prime1_sz > 47000


@pytest.mark.parametrize("section", ["WELCOME", "CREDITS"])
def test_extract_readme(tmp_path, section: str):
    # Setup
    args = MagicMock()
    args.output_dir = tmp_path
    args.section = section

    # Run
    website.export_readme_sections_logic(args)

    # Check
    old = get_readme_section(section)
    new = tmp_path.joinpath(f"{section.lower()}.md").read_text()

    assert old == new


def test_extract_game_data(tmp_path, test_files_dir):
    # Setup
    games_dir = tmp_path.joinpath("games_data")
    games_dir.mkdir(exist_ok=True)

    args = MagicMock()
    args.game = None
    args.games_dir = games_dir
    args.covers_dir = games_dir

    # Run
    website.extract_game_data_logic(args)

    # Check
    assert games_dir.joinpath("blank.png").exists()

    data = games_dir.joinpath("blank.md").read_text()
    expected_data = test_files_dir.joinpath("blank_game_web_info.md").read_text()
    assert data == expected_data
