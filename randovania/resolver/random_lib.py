from random import Random
from typing import Iterator, List, TypeVar

T = TypeVar('T')


def shuffle(rng: Random, x: Iterator[T]) -> List[T]:
    """
    Shuffles a copy of the given iterator.
    :param rng:
    :param x:
    :return:
    """
    result = list(x)
    rng.shuffle(result)
    return result
