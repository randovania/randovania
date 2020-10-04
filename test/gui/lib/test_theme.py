import pytest

from randovania.gui.lib import theme


@pytest.mark.parametrize("active", [False, True])
def test_set_dark_theme(skip_qtbot, active):
    theme.set_dark_theme(active)
