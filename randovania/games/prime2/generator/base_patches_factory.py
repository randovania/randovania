import copy
from random import Random

from randovania.game_description.assignment import NodeConfigurationAssignment
from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.hint import (Hint, HintDarkTemple,
                                              HintItemPrecision,
                                              HintLocationPrecision, HintType)
from randovania.game_description.requirements import (RequirementAnd,
                                                      ResourceRequirement)
from randovania.game_description.resources import search
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.world.node import (ConfigurableNode,
                                                    LogbookNode)
from randovania.game_description.world.world_list import WorldList
from randovania.games.prime2.layout.echoes_configuration import \
    EchoesConfiguration
from randovania.games.prime2.layout.translator_configuration import \
    LayoutTranslatorRequirement
from randovania.generator.base_patches_factory import (HintTargetPrecision, PrimeTrilogyBasePatchesFactory,
                                                       MissingRng)
from randovania.lib.enum_lib import iterate_enum


class EchoesBasePatchesFactory(PrimeTrilogyBasePatchesFactory):
    def configurable_node_assignment(self, configuration: EchoesConfiguration, game: GameDescription,
                                     rng: Random) -> NodeConfigurationAssignment:
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

        result = {}

        scan_visor = search.find_resource_info_with_long_name(
            game.resource_database.item,
            "Scan Visor"
        )
        scan_visor_req = ResourceRequirement(scan_visor, 1, False)

        for node in game.world_list.all_nodes:
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
            result[identifier] = RequirementAnd([
                scan_visor_req,
                ResourceRequirement(translator, 1, False),
            ])

        return result

    def indices_with_hint(self, configuration: EchoesConfiguration, game: GameDescription, rng: Random,
                          patches: GamePatches, world_list: WorldList) -> list[HintTargetPrecision]:
        return [
            (PickupIndex(24), HintLocationPrecision.LIGHT_SUIT_LOCATION, HintItemPrecision.DETAILED),  # Light Suit
            (PickupIndex(43), HintLocationPrecision.GUARDIAN, HintItemPrecision.DETAILED),  # Dark Suit (Amorbis)
            (PickupIndex(79), HintLocationPrecision.GUARDIAN, HintItemPrecision.DETAILED),  # Dark Visor (Chykka)
            (PickupIndex(115), HintLocationPrecision.GUARDIAN, HintItemPrecision.DETAILED),
            # Annihilator Beam (Quadraxis)
        ]

    def add_other_hints(self, patches: GamePatches, all_logbook_nodes: list[LogbookNode]) -> GamePatches:
        # Dark Temple hints
        temple_hints = list(iterate_enum(HintDarkTemple))
        while all_logbook_nodes and temple_hints:
            logbook_asset = all_logbook_nodes.pop().resource()
            patches = patches.assign_hint(logbook_asset, Hint(HintType.RED_TEMPLE_KEY_SET, None,
                                                              dark_temple=temple_hints.pop(0)))
        return patches
