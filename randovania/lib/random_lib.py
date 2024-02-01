from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator, Mapping
    from random import Random

T = TypeVar("T")


def shuffle(rng: Random, x: Iterator[T]) -> list[T]:
    """
    Shuffles a copy of the given iterator.
    :param rng:
    :param x:
    :return:
    """
    result = list(x)
    rng.shuffle(result)
    return result


def iterate_with_weights(
    items: Iterable[T],
    item_weights: Mapping[T, float],
    rng: Random,
) -> Iterator[T]:
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
        pickup_node = rng.choices(item_list, weights)[0]

        # Remove the pickup_node from the potential list, along with its weight
        index = item_list.index(pickup_node)
        item_list.pop(index)
        weights.pop(index)

        yield pickup_node


def select_element_with_weight(weighted_items: Mapping[T, float], rng: Random) -> T:
    return next(iterate_with_weights(items=list(weighted_items.keys()), item_weights=weighted_items, rng=rng))


def random_key(d: dict[T, Any], rng: Random) -> T:
    return rng.choice(list(d.keys()))


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
