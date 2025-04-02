from __future__ import annotations

from random import Random

from randovania.lib import random_lib


def test_select_weighted_action_weighted():
    rng = Random(1500)
    a = object()
    b = object()
    actions = {a: 1.0, b: 2.0}

    # Run
    r = random_lib.select_element_with_weight_and_uniform_fallback(rng, actions)

    # Assert
    assert r == a


def test_select_weighted_action_zero_weight():
    rng = Random(1500)
    a = object()
    b = object()
    actions = {a: 0.0, b: 0.0}

    # Run
    r = random_lib.select_element_with_weight_and_uniform_fallback(rng, actions)

    # Assert
    assert r == b
