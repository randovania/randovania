from randovania.games.prime import claris_random


def test_random_a():
    r = claris_random.Random(1965278358)
    for i in range(20):
        arg = 119 - i
        num = r.next_with_max(arg)
        assert num <= arg
