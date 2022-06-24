import os
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
    magmoor_caverns_sz = os.path.getsize(os.path.join(tmp_path, "Metroid Prime", "Magmoor Caverns.html"))
    assert magmoor_caverns_sz > 5000
