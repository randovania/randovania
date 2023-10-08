from __future__ import annotations

from random import Random
from unittest.mock import MagicMock

from randovania.generator.filler import retcon
from randovania.generator.filler.action import Action


def test_select_weighted_action_weighted():
    rng = Random(1500)
    a = Action([MagicMock()])
    b = Action([MagicMock()])
    actions = {a: 1.0, b: 2.0}

    # Run
    r = retcon.select_weighted_action(rng, actions)

    # Assert
    assert r == a


def test_select_weighted_action_zero_weight():
    rng = Random(1500)
    a = Action([MagicMock()])
    b = Action([MagicMock()])
    actions = {a: 0.0, b: 0.0}

    # Run
    r = retcon.select_weighted_action(rng, actions)

    # Assert
    assert r == b
