from random import Random

from randovania.generator.filler import retcon


def test_select_weighted_action_weighted():
    rng = Random(1500)
    a = object()
    b = object()
    actions = {a: 1, b: 2}

    # Run
    r = retcon.select_weighted_action(rng, actions)

    # Assert
    assert r == a


def test_select_weighted_action_zero_weight():
    rng = Random(1500)
    a = object()
    b = object()
    actions = {a: 0, b: 0}

    # Run
    r = retcon.select_weighted_action(rng, actions)

    # Assert
    assert r == b
