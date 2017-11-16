import pprint

import randovania.games.prime.claris_random as rng


def test_random_a():
    r = rng.Random(1965278358)
    for i in range(20):
        arg = 119 - i
        num = r.next_with_max(arg)
        assert num <= arg
