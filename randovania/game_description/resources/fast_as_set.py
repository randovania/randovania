import itertools
import typing

from randovania.game_description.requirements.base import Requirement
from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.game_description.requirements.requirement_list import RequirementList
from randovania.game_description.requirements.requirement_or import RequirementOr
from randovania.game_description.requirements.requirement_template import RequirementTemplate
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.resource_database import ResourceDatabase


class UnableToAvoidError(Exception):
    pass


def _internal_fast_as(req: Requirement, db: ResourceDatabase) -> typing.Iterable[RequirementList]:
    if isinstance(req, RequirementTemplate):
        req = req.template_requirement(db)

    if isinstance(req, ResourceRequirement):
        yield RequirementList([req])

    elif isinstance(req, RequirementAnd):
        ret = []
        multiply = []

        for it in req.items:
            if isinstance(it, RequirementTemplate):
                it = it.template_requirement(db)

            if isinstance(it, ResourceRequirement):
                ret.append(it)

            elif isinstance(it, RequirementAnd):
                for recursive in _internal_fast_as(it, db):
                    ret.extend(recursive.values())

            elif isinstance(it, RequirementOr):
                multiply.append(list(_internal_fast_as(it, db)))

            else:
                raise UnableToAvoidError()

        if multiply:
            for m in itertools.product(*multiply):
                yield RequirementList(itertools.chain(ret, *[k.values() for k in m]))
        else:
            yield RequirementList(ret)

    elif isinstance(req, RequirementOr):
        for it in req.items:
            yield from _internal_fast_as(it, db)

    else:
        raise UnableToAvoidError()


def fast_as_alternatives(req: Requirement, db: ResourceDatabase) -> typing.Iterable[RequirementList]:
    """
    Equivalent to req.as_set(db).alternatives, but attempt to be faster
    """
    try:
        yield from list(_internal_fast_as(req, db))

    except UnableToAvoidError:
        yield from req.as_set(db).alternatives
