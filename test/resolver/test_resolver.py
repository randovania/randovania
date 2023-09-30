from __future__ import annotations

import pytest

from randovania.layout.layout_description import LayoutDescription
from randovania.resolver import debug, resolver


@pytest.mark.skip_resolver_tests()
@pytest.mark.parametrize(
    "seed_name",
    [
        "prime2/seed_a.rdvgame",
        "prime3/corruption_seed_a.rdvgame",
        "prime1/prime1-vanilla.rdvgame",
        "prime2/prime2_seed_b.rdvgame",
        "blank/issue-3717.rdvgame",
    ],
)
async def test_resolver_with_log_file(test_files_dir, seed_name: str):
    # Setup
    debug.set_level(2)

    description = LayoutDescription.from_file(test_files_dir.joinpath("rdvgames", seed_name))
    configuration = description.get_preset(0).configuration
    patches = description.all_patches[0]

    # Run
    final_state_by_resolve = await resolver.resolve(configuration=configuration, patches=patches)

    # Assert
    assert final_state_by_resolve is not None
