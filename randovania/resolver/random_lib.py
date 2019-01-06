from random import Random
from typing import Iterator, List, TypeVar, Dict

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


def iterate_with_weights(items: List[T],
                         item_weights: Dict[T, float],
                         rng: Random,
                         ) -> Iterator[T]:
    """
    Iterates over the given list randomly, with each item having the probability listed in item_weigths
    :param items:
    :param item_weights:
    :param rng:
    :return:
    """

    items = list(items)
    weights = [max(item_weights[action], 0) for action in items]

    while items and any(weight > 0 for weight in weights):
        pickup_node = rng.choices(items, weights)[0]

        # Remove the pickup_node from the potential list, along with it's weight
        index = items.index(pickup_node)
        items.pop(index)
        weights.pop(index)

        yield pickup_node
