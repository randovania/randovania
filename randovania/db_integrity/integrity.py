from collections.abc import Iterator

from randovania.game_description.db.node import NodeContext
from randovania.game_description.game_description import GameDescription
from randovania.game_description.requirements.array_base import RequirementArrayBase
from randovania.game_description.requirements.base import Requirement
from randovania.game_description.requirements.resource_requirement import ResourceRequirement


def needed_resources_partly_satisfied(
    req: Requirement, resources: tuple[str, tuple[str, ...]], context: NodeContext, req_cache: dict
) -> bool:
    if req in req_cache:
        req_set = req_cache[req]
    else:
        req_set = req.as_set(context)
        req_cache[req] = req_set

    counter = 0
    res_key = resources[0]
    res_values = resources[1]
    for alternative in req_set.alternatives:
        # Either the key must not be present, or the key is present with all values.
        if not any(res_key == item.resource.short_name for item in alternative.values()):
            counter += 1
        elif all(any(resource == item.resource.short_name for item in alternative.values()) for resource in res_values):
            counter += 1

    return counter != len(req_set.alternatives)


def does_requirement_contain_resource(req: Requirement, resource: str) -> bool:
    if isinstance(req, ResourceRequirement):
        if req.resource.short_name == resource and req.amount == 1:
            return True
        return False
    if isinstance(req, RequirementArrayBase):
        return any(does_requirement_contain_resource(subreq, resource) for subreq in req.items)
    return False


def items_to_be_replaced_by_templates(
    game: GameDescription, context: NodeContext, items_to_templates: dict[str, str]
) -> Iterator[str]:
    for source_node in game.region_list.iterate_nodes():
        for destination_node, req in game.region_list.potential_nodes_from(source_node, context):
            for resource, template in items_to_templates.items():
                if does_requirement_contain_resource(req, resource):
                    yield (
                        f"{source_node.identifier.as_string} -> {destination_node.identifier.as_string} is using "
                        f'the resource "{resource}" directly than using the template "{template}".'
                    )


def resources_to_use_together(
    game: GameDescription, context: NodeContext, combined_resources: dict[str, tuple[str, ...]]
) -> Iterator[str]:
    requirement_cache = {}

    for source_node in game.region_list.iterate_nodes():
        for destination_node, req in game.region_list.potential_nodes_from(source_node, context):
            for resource_key, resource_value in combined_resources.items():
                if needed_resources_partly_satisfied(req, (resource_key, resource_value), context, requirement_cache):
                    yield (
                        f"{source_node.identifier.as_string} -> {destination_node.identifier.as_string} contains "
                        f'"{resource_key}" but not "{resource_value}"'
                    )
