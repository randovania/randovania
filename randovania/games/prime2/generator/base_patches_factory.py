import copy
from random import Random
from typing import Iterator

from randovania.game_description.assignment import NodeConfigurationAssociation
from randovania.game_description.game_description import GameDescription
from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources import search
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.world.configurable_node import ConfigurableNode
from randovania.games.prime2.layout.echoes_configuration import EchoesConfiguration
from randovania.games.prime2.layout.translator_configuration import LayoutTranslatorRequirement
from randovania.generator.base_patches_factory import (PrimeTrilogyBasePatchesFactory, MissingRng)


class EchoesBasePatchesFactory(PrimeTrilogyBasePatchesFactory):
    def configurable_node_assignment(self, configuration: EchoesConfiguration, game: GameDescription,
                                     rng: Random) -> Iterator[NodeConfigurationAssociation]:
        """
        :param configuration:
        :param game:
        :param rng:
        :return:
        """

        all_choices = list(LayoutTranslatorRequirement)
        all_choices.remove(LayoutTranslatorRequirement.RANDOM)
        all_choices.remove(LayoutTranslatorRequirement.RANDOM_WITH_REMOVED)
        without_removed = copy.copy(all_choices)
        without_removed.remove(LayoutTranslatorRequirement.REMOVED)
        random_requirements = {LayoutTranslatorRequirement.RANDOM, LayoutTranslatorRequirement.RANDOM_WITH_REMOVED}

        result = []

        scan_visor = search.find_resource_info_with_long_name(
            game.resource_database.item,
            "Scan Visor"
        )
        scan_visor_req = ResourceRequirement.simple(scan_visor)

        for node in game.world_list.iterate_nodes():
            if not isinstance(node, ConfigurableNode):
                continue

            identifier = game.world_list.identifier_for_node(node)
            requirement = configuration.translator_configuration.translator_requirement[identifier]
            if requirement in random_requirements:
                if rng is None:
                    raise MissingRng("Translator")
                requirement = rng.choice(all_choices if requirement == LayoutTranslatorRequirement.RANDOM_WITH_REMOVED
                                         else without_removed)

            translator = game.resource_database.get_by_type_and_index(ResourceType.ITEM, requirement.item_name)
            result.append((identifier, RequirementAnd([
                scan_visor_req,
                ResourceRequirement.simple(translator),
            ])))

        return result
