from __future__ import annotations

import copy
import itertools
from typing import TYPE_CHECKING

from randovania.game_description.requirements.node_requirement import NodeRequirement
from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.game_description.requirements.requirement_or import RequirementOr
from randovania.game_description.requirements.requirement_template import RequirementTemplate
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.graph.graph_requirement import GraphRequirementList, GraphRequirementSet, create_requirement_set

if TYPE_CHECKING:
    from randovania.game_description.db.node_identifier import NodeIdentifier
    from randovania.game_description.game_database_view import ResourceDatabaseView
    from randovania.game_description.requirements.base import Requirement
    from randovania.game_description.resources.resource_collection import ResourceCollection
    from randovania.game_description.resources.resource_info import ResourceInfo
    from randovania.graph.world_graph import WorldGraph


class GraphRequirementConverter:
    def __init__(
        self,
        resource_database: ResourceDatabaseView,
        graph: WorldGraph,
        static_resources: ResourceCollection,
        damage_multiplier: float,
    ):
        self.resource_database = resource_database
        self.graph = graph
        self.static_resources = static_resources
        self.damage_multiplier = damage_multiplier
        self._cache: dict[Requirement, GraphRequirementSet] = {}
        self._template_cache: dict[str, list[GraphRequirementList] | None] = {}

    def resource_for_node(self, identifier: NodeIdentifier) -> ResourceInfo:
        for node in self.graph.nodes:
            if node.identifier == identifier:
                return self.graph.resource_info_for_node(node)
        raise KeyError(f"Unknown identifier: {identifier}")

    def _convert_template(self, name: str) -> GraphRequirementList | GraphRequirementSet:
        if name in self._template_cache:
            cached = self._template_cache[name]
            if cached is None:
                raise ValueError(f"Template {name} has a loop!")

            if len(cached) == 1:
                return copy.copy(cached[0])
            return create_requirement_set(cached, copy_entries=True)

        requirement = self.resource_database.get_template_requirement(name).requirement
        result = self._internal_convert(requirement)

        if isinstance(result, GraphRequirementList):
            self._template_cache[name] = [result]
        else:
            if not result.is_frozen():
                result.optimize_alternatives()
            self._template_cache[name] = [copy.copy(it) for it in result.alternatives]

        return result

    def _convert_or(self, requirement: RequirementOr) -> GraphRequirementList | GraphRequirementSet:
        if len(requirement.items) == 1:
            return self._internal_convert(requirement.items[0])

        result = GraphRequirementSet()

        for item in requirement.items:
            converted = self._internal_convert(item)
            if isinstance(converted, GraphRequirementList):
                result.add_alternative(converted)
            else:
                result.extend_alternatives(converted.alternatives)

        return result

    def _convert_and(self, requirement: RequirementAnd) -> GraphRequirementList | GraphRequirementSet:
        if len(requirement.items) == 1:
            return self._internal_convert(requirement.items[0])

        nested_or: list[GraphRequirementSet] = []
        nested_and = GraphRequirementList(self.resource_database)

        for item in requirement.items:
            converted = self._internal_convert(item)
            if converted == GraphRequirementSet.impossible():
                return converted

            if isinstance(converted, GraphRequirementList):
                if not nested_and.and_with(converted):
                    return GraphRequirementSet.impossible()
            else:
                nested_or.append(converted)

        if not nested_or:
            return nested_and

        result = GraphRequirementSet()

        alt: tuple[GraphRequirementList, ...]
        for alt in itertools.product(*[it.alternatives for it in nested_or]):
            skip = False
            entry = copy.copy(nested_and)
            for other in alt:
                if not entry.and_with(other):
                    skip = True
                    break

            if not skip:
                result.add_alternative(entry)

        return result

    def _internal_convert(self, requirement: Requirement) -> GraphRequirementList | GraphRequirementSet:
        if isinstance(requirement, RequirementTemplate):
            return self._convert_template(requirement.template_name)

        if isinstance(requirement, RequirementOr):
            return self._convert_or(requirement)

        elif isinstance(requirement, RequirementAnd):
            return self._convert_and(requirement)

        else:
            if isinstance(requirement, NodeRequirement):
                resource = self.resource_for_node(requirement.node_identifier)
                negate = False
                amount = 1
            else:
                assert isinstance(requirement, ResourceRequirement)
                resource = requirement.resource
                negate = requirement.negate
                amount = requirement.amount
                if resource.resource_type.is_damage():
                    amount = int(amount * self.damage_multiplier)

            result = GraphRequirementList(self.resource_database)
            result.add_resource(resource, amount, negate)

            if self.static_resources.is_resource_set(resource):
                if result.satisfied(self.static_resources, 0):
                    return GraphRequirementList(self.resource_database)
                elif not isinstance(resource, ItemResourceInfo) or resource.max_capacity <= 1:
                    return GraphRequirementSet.impossible()

            return result

    def convert_db(self, requirement: Requirement) -> GraphRequirementSet:
        if requirement in self._cache:
            return self._cache[requirement]

        result = self._internal_convert(requirement)
        if isinstance(result, GraphRequirementList):
            req_set = GraphRequirementSet()
            req_set.add_alternative(result)
            req_set.freeze()
            if req_set.is_trivial():
                req_set = GraphRequirementSet.trivial()
            self._cache[requirement] = req_set
            return req_set
        else:
            if not result.is_frozen():
                result.optimize_alternatives()
                result.freeze()

            if result.is_trivial():
                result = GraphRequirementSet.trivial()
            self._cache[requirement] = result
            return result
