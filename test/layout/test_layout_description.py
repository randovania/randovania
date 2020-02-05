import pickle

import pytest

from randovania.layout.trick_level import LayoutTrickLevel


@pytest.mark.parametrize("value", LayoutTrickLevel)
def test_pickle_trick_level(value: LayoutTrickLevel):
    assert pickle.loads(pickle.dumps(value)) == value
