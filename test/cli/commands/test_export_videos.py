from __future__ import annotations

from unittest.mock import MagicMock

from randovania.cli import database


def test_export_videos(tmp_path):
    # Setup
    args = MagicMock()
    args.game = None
    args.output_dir = tmp_path

    # Run
    database.export_videos_command_logic(args)

    # Check
    magmoor_caverns_sz = tmp_path.joinpath("Metroid Prime", "Magmoor Caverns.html").stat().st_size
    assert magmoor_caverns_sz > 5000
