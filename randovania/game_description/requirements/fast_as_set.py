from __future__ import annotations

import itertools
import typing

from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.game_description.requirements.requirement_list import RequirementList
from randovania.game_description.requirements.requirement_or import RequirementOr
from randovania.game_description.requirements.requirement_template import RequirementTemplate
from randovania.game_description.requirements.resource_requirement import ResourceRequirement

if typing.TYPE_CHECKING:
    from randovania.game_description.db.node import NodeContext
    from randovania.game_description.requirements.base import Requirement


class UnableToAvoidError(Exception):
    pass


def _internal_fast_as(req: Requirement, context: NodeContext) -> typing.Iterable[RequirementList]:
    if isinstance(req, RequirementTemplate):
        req = req.template_requirement(context.database)

    if isinstance(req, ResourceRequirement):
        yield RequirementList([req])

    elif isinstance(req, RequirementAnd):
        parts = [_internal_fast_as(it, context) for it in req.items]
        product = itertools.product(*parts)
        for branch in product:
            yield RequirementList(itertools.chain(*[k.values() for k in branch]))

    elif isinstance(req, RequirementOr):
        for it in req.items:
            yield from _internal_fast_as(it, context)

    else:
        raise UnableToAvoidError


def fast_as_alternatives(req: Requirement, context: NodeContext) -> typing.Iterable[RequirementList]:
    """
    Equivalent to req.as_set(db).alternatives, but attempt to be faster
    """
    try:
        yield from list(_internal_fast_as(req, context))

    except UnableToAvoidError:
        yield from req.as_set(context).alternatives
