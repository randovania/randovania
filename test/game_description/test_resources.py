import pytest

from randovania.game_description.resources import merge_resources


@pytest.mark.parametrize(["a", "b", "result"], [
    ({"a": 5}, {"b": 6}, {"a": 5, "b": 6}),
    ({"a": 5}, {"a": 6}, {"a": 11}),
])
def test_merge_resources(a, b, result):
    assert merge_resources(a, b) == result
