import dataclasses
from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class ActionWeights:
    DEFAULT_INDICES_WEIGHT: Final[float] = 1.0
    """
    The default value by how much an action's weight will be increased during generation if
    the action unlocks Pickup nodes.
    """
    DEFAULT_EVENTS_WEIGHT: Final[float] = 0.5
    """
    The default value by how much an action's weight will be increased during generation if
    the action unlocks Event nodes.
    """
    DEFAULT_HINTS_WEIGHT: Final[float] = 1.0
    """
    The default value by how much an action's weight will be increased during generation if
    the action unlocks Hint nodes.
    """
    DANGEROUS_ACTION_MULTIPLIER: Final[float] = 0.75
    """When weighting an action, indicates by how much the weight will be multiplied if the action is unsafe."""

    ADDITIONAL_NODES_WEIGHT_MULTIPLIER: Final[float] = 0.01
    """
    When calculating backup weights, indicates by how much the weight will be multiplied per node that is unlocked.
    """
    VICTORY_WEIGHT: Final[float] = 1000
    """
    When weighting an action, indicates by how much the weight will be multiplied if it unlocks the victory condition.
    """

    indices_weight: float = dataclasses.field(default=DEFAULT_INDICES_WEIGHT)
    """
    While weighting an action during generation, indicates the weight that will be added if
    the action unlocks Pickup nodes.
    """

    events_weight: float = dataclasses.field(default=DEFAULT_EVENTS_WEIGHT)
    """
    While weighting an action during generation, indicates the weight that will be added if
    the action unlocks Event nodes.
    """

    hints_weight: float = dataclasses.field(default=DEFAULT_HINTS_WEIGHT)
    """
    While weighting an action during generation, indicates the weight that will be added if
    the action unlocks Hint nodes.
    """
