import pytest

from randovania.layout.layout_description import LayoutDescription
from randovania.resolver import resolver, debug


@pytest.mark.skip_resolver_tests
@pytest.mark.parametrize("seed_name", ["seed_a.rdvgame", "corruption_seed_a.rdvgame"])
@pytest.mark.asyncio
async def test_resolver_with_log_file(test_files_dir, seed_name: str):
    # Setup
    debug.set_level(2)

    description = LayoutDescription.from_file(test_files_dir.joinpath("log_files", seed_name))
    configuration = description.permalink.presets[0].configuration
    patches = description.all_patches[0]

    # Run
    final_state_by_resolve = await resolver.resolve(configuration=configuration,
                                                    patches=patches)

    # Assert
    assert final_state_by_resolve is not None
