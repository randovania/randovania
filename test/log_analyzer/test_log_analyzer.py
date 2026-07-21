from pathlib import Path

from randovania.log_analyzer import log_analyzer
from test.conftest import COOP_RDVGAMES, SOLO_RDVGAMES


def test_create_report():
    log_dir = Path(__file__).parents[1].joinpath("test_files", "log_files")
    layout_names = SOLO_RDVGAMES + COOP_RDVGAMES
    seed_files = [log_dir.joinpath(layout_name) for layout_name, _ in layout_names]

    result = log_analyzer.create_report(seed_files, None, False, False)
    # Asserting that it has enough data. This is most the make sure the code still runs, not much if it's still correct.
    assert len(result["regions"]) >= 250
    assert len(result["items"]) >= 830
