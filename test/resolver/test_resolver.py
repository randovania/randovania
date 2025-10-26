from __future__ import annotations

import typing

import pytest

from randovania.layout.layout_description import LayoutDescription
from randovania.resolver import debug, resolver
from test.conftest import SOLO_RDVGAMES

if typing.TYPE_CHECKING:
    import _pytest.python


@pytest.mark.benchmark
@pytest.mark.skip_resolver_tests
async def test_resolver_with_log_file(test_files_dir, layout_name, is_valid):
    # Setup
    debug.set_level(2)

    description = LayoutDescription.from_file(test_files_dir.joinpath("log_files", layout_name))
    configuration = description.get_preset(0).configuration
    patches = description.all_patches[0]

    # Run
    final_state_by_resolve = await resolver.resolve(configuration=configuration, patches=patches)

    # Assert
    if is_valid:
        assert final_state_by_resolve is not None
    else:
        assert final_state_by_resolve is None


def pytest_generate_tests(metafunc: _pytest.python.Metafunc) -> None:
    metafunc.parametrize(
        ["layout_name", "is_valid"],
        [(layout_name, is_valid) for layout_name, is_valid in SOLO_RDVGAMES if is_valid is not None],
    )
