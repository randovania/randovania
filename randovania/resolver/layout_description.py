from typing import NamedTuple, Tuple

from randovania.resolver.layout_configuration import LayoutConfiguration


class SolverPath(NamedTuple):
    node_name: str
    previous_nodes: Tuple[str, ...]


class LayoutDescription(NamedTuple):
    configuration: LayoutConfiguration
    version: str
    pickup_mapping: Tuple[int, ...]
    solver_path: Tuple[SolverPath, ...]
