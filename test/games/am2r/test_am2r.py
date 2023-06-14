import pytest
from randovania.game_description import derived_nodes, default_database
from randovania.game_description.db.area_identifier import AreaIdentifier
from randovania.game_description.db.dock import DockWeaknessDatabase
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.game_description.db.region_list import RegionList
from randovania.game_description.db.teleporter_node import TeleporterNode
from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_description import GameDescription
from randovania.game_description.requirements.base import Requirement
from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.game_description.requirements.requirement_list import SatisfiableRequirements
from randovania.game_description.requirements.requirement_or import RequirementOr
from randovania.game_description.requirements.requirement_template import RequirementTemplate
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import ResourceInfo, ResourceGainTuple, ResourceCollection
from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo
from randovania.games.game import RandovaniaGame

resource_list = [
    # Tricks
    ("IBJ", "Can Use Bombs"),
    ("Mid-Air Morph", "Morph Ball"),
    ("Shinesparking", "Speed Booster"),
    ("Morph Glide", "Morph Ball"),
    ("ShortCharge", "Speed Booster"),
    ("DiagonalIBJ", "Can Use Bombs"),
    ("ChargedBombJump", "Can Use Charged Bomb Jump"),
    # Items
    ("Bombs", "Morph Ball"),
    ("Spider Ball", "Morph Ball"),
    ("Spring Ball", "Morph Ball"),
    ("Power Bombs", "Morph Ball")
]


def does_requirement_contain_resource(requirement, resource, db):
    if isinstance(requirement, RequirementTemplate):
        if requirement.template_name == resource:
            return True
        template_req = requirement.template_requirement(db)
        return does_requirement_contain_resource(template_req, resource, db)
    if isinstance(requirement, ResourceRequirement):
        if requirement.pretty_text == resource:
            return True
        return False
    for subreq in requirement.items:
        temp_result = does_requirement_contain_resource(subreq, resource, db)
        if temp_result:
            return temp_result
    return False


def test_all_tricks_should_have_proper_requirements():
    game = default_database.game_description_for(RandovaniaGame.AM2R)
    rl = game.region_list
    db = game.resource_database
    expected_dict = {}
    database_dict = {}
    for i in range(len(resource_list)):
        database_dict[resource_list[i]] = []
        expected_dict[resource_list[i]] = []

    for node in rl.all_nodes:
        for dest_node, requirements in rl.area_connections_from(node):
            for required_resources in resource_list:
                size = len(required_resources)
                required_resource_collection = {}
                for i in range(size):
                    required_resource_collection[i] = False

                for i in range(size):
                    required_resource_collection[i] = \
                        does_requirement_contain_resource(requirements, required_resources[i], db)
                    if not required_resource_collection[i]:
                        break

                if len(set(required_resource_collection.values())) > 1:
                    database_dict[required_resources].append(
                        (f"{node.name} ({node.identifier.area_name})",
                         f"{dest_node.name} ({dest_node.identifier.area_name})")
                    )

    assert database_dict == expected_dict
