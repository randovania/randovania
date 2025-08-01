from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator, Mapping
    from random import Random

T = TypeVar("T")


def shuffle[T](rng: Random, x: Iterator[T]) -> list[T]:
    """
    Shuffles a copy of the given iterator.
    :param rng:
    :param x:
    :return:
    """
    result = list(x)
    rng.shuffle(result)
    return result


def iterate_with_weights(rng: Random, items: Iterable[T], item_weights: Mapping[T, float]) -> Iterator[T]:
    """
    Iterates over the given list randomly, with each item having the probability listed in item_weigths
    :param items:
    :param item_weights:
    :param rng:
    :return:
    """

    item_list = list(items)
    weights = [max(item_weights[action], 0) for action in item_list]

    while item_list and any(weight > 0 for weight in weights):
        item = rng.choices(item_list, weights)[0]

        # Remove the pickup_node from the potential list, along with its weight
        index = item_list.index(item)
        item_list.pop(index)
        weights.pop(index)

        yield item


def select_element_with_weight[T](rng: Random, weighted_items: Mapping[T, float]) -> T:
    """
    Choose a random element, with each one having a custom weight.
    :param rng: The random object to use.
    :param weighted_items: The weights
    :return: One of the keys in weighted_items
    """
    return next(iterate_with_weights(rng=rng, items=list(weighted_items.keys()), item_weights=weighted_items))


def select_element_with_weight_and_uniform_fallback[T](rng: Random, weighted_items: Mapping[T, float]) -> T:
    """
    Same as `select_element_with_weight`, but if all elements have weight 0 then one is selected uniformly.
    """
    try:
        return select_element_with_weight(rng=rng, weighted_items=weighted_items)
    except StopIteration:
        return rng.choice(list(weighted_items.keys()))


def create_weighted_list(
    rng: Random,
    current: list[T],
    factory: Callable[[], list[T]],
) -> list[T]:
    """
    Ensures we always have a non-empty list.
    :param rng:
    :param current:
    :param factory:
    :return:
    """
    if not current:
        current = factory()
        rng.shuffle(current)

    return current
