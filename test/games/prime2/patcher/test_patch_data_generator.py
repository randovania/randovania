import dataclasses
import json
from unittest.mock import MagicMock

import pytest
from frozendict import frozendict

import randovania
from randovania.exporter import pickup_exporter
from randovania.game_description.assignment import PickupTarget
from randovania.game_description.requirements import RequirementAnd, ResourceRequirement
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.pickup_entry import PickupModel, ConditionalResources
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_info import ResourceCollection
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.world.area_identifier import AreaIdentifier
from randovania.game_description.world.node_identifier import NodeIdentifier
from randovania.games.game import RandovaniaGame
from randovania.games.prime2.exporter import patch_data_factory
from randovania.games.prime2.layout.echoes_configuration import EchoesConfiguration
from randovania.games.prime2.layout.echoes_cosmetic_patches import EchoesCosmeticPatches
from randovania.games.prime2.layout.hint_configuration import SkyTempleKeyHintMode, HintConfiguration
from randovania.generator.item_pool import pickup_creator, pool_creator
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.game_description import default_database
from randovania.layout.base.major_item_state import MajorItemState
from randovania.layout.base.pickup_model import PickupModelStyle
from randovania.game_description.default_database import default_prime2_memo_data
from randovania.layout.layout_description import LayoutDescription
from randovania.layout.lib.teleporters import TeleporterShuffleMode


def test_create_starting_popup_empty(default_echoes_configuration, echoes_resource_database):
    starting_items = ResourceCollection.with_database(echoes_resource_database)

    # Run
    result = patch_data_factory._create_starting_popup(default_echoes_configuration,
                                                       echoes_resource_database,
                                                       starting_items)

    # Assert
    assert result == []


def test_create_starting_popup_items(default_echoes_configuration, echoes_resource_database):
    starting_items = ResourceCollection.from_dict({
        echoes_resource_database.get_item_by_name("Missile"): 15,
        echoes_resource_database.energy_tank: 3,
        echoes_resource_database.get_item_by_name("Dark Beam"): 1,
        echoes_resource_database.get_item_by_name("Screw Attack"): 1,
    })

    # Run
    result = patch_data_factory._create_starting_popup(default_echoes_configuration,
                                                       echoes_resource_database,
                                                       starting_items)

    # Assert
    assert result == [
        'Extra starting items:',
        'Dark Beam, 3 Energy Tank, 15 Missiles, Screw Attack'
    ]


def test_adjust_model_name(randomizer_data):
    # Setup
    patcher_data = {
        "pickups": [
            {"model": {"game": "prime2", "name": "DarkVisor"}},
            {"model": {"game": "prime2", "name": "SkyTempleKey"}},
            {"model": {"game": "prime2", "name": "MissileExpansion"}},
            {"model": {"game": "prime1", "name": "Boost Ball"}},
            {"model": {"game": "prime1", "name": "Plasma Beam"}},
        ]
    }

    # Run
    patch_data_factory.adjust_model_name(patcher_data, randomizer_data)

    # Assert
    assert patcher_data == {
        "pickups": [
            {"model_index": 11, "sound_index": 0, "jingle_index": 1},
            {"model_index": 38, "sound_index": 1, "jingle_index": 2},
            {"model_index": 22, "sound_index": 0, "jingle_index": 0},
            {"model_index": 18, "sound_index": 0, "jingle_index": 1},
            {"model_index": 30, "sound_index": 0, "jingle_index": 1},
        ]
    }


def test_add_header_data_to_result():
    # Setup
    description = MagicMock()
    description.shareable_word_hash = "<shareable_word_hash>"
    description.shareable_hash = "<shareable_hash>"
    expected = {
        "permalink": "-permalink-",
        "seed_hash": "- <shareable_word_hash> (<shareable_hash>)",
        "randovania_version": randovania.VERSION,
        'shareable_hash': '<shareable_hash>',
        'shareable_word_hash': '<shareable_word_hash>',
    }
    result = {}

    # Run
    patch_data_factory._add_header_data_to_result(description, result)

    # Assert
    assert json.loads(json.dumps(result)) == expected


def test_create_spawn_point_field(echoes_game_description, empty_patches):
    # Setup
    resource_db = echoes_game_description.resource_database

    loc = AreaIdentifier("Temple Grounds", "Hive Chamber B")
    patches = empty_patches.assign_starting_location(loc).assign_extra_initial_items([
        (resource_db.get_item("MorphBall"), 3),
    ])

    capacities = [
        {'amount': 3 if item.short_name == "MorphBall" else 0, 'index': item.extra["item_id"]}
        for item in resource_db.item
    ]

    # Run
    result = patch_data_factory._create_spawn_point_field(patches, echoes_game_description)

    # Assert
    assert result == {
        "location": {
            "world_asset_id": 1006255871,
            "area_asset_id": 494654382,
        },
        "amount": capacities,
        "capacity": capacities,
    }


def test_create_elevators_field_no_elevator(empty_patches, echoes_game_description):
    # Setup
    # Run
    with pytest.raises(ValueError) as exp:
        patch_data_factory._create_elevators_field(empty_patches, echoes_game_description)

    # Assert
    assert str(exp.value) == "Invalid elevator count. Expected 22, got 0."


@pytest.mark.parametrize("vanilla_gateway", [False, True])
def test_create_elevators_field_elevators_for_a_seed(vanilla_gateway: bool,
                                                     echoes_game_description, empty_patches):
    # Setup
    elevator_connection = echoes_game_description.get_default_elevator_connection()

    def add(world: str, area: str, node: str, target_world: str, target_area: str):
        elevator_connection[NodeIdentifier.create(world, area, node)] = AreaIdentifier(target_world, target_area)

    add("Temple Grounds", "Temple Transport C", "Elevator to Great Temple - Temple Transport C",
        "Sanctuary Fortress", "Transport to Agon Wastes")
    add("Temple Grounds", "Transport to Agon Wastes", "Elevator to Agon Wastes - Transport to Temple Grounds",
        "Torvus Bog", "Transport to Agon Wastes")

    if not vanilla_gateway:
        add("Temple Grounds", "Sky Temple Gateway", "Teleport to Great Temple - Sky Temple Energy Controller",
            "Great Temple", "Sanctum")

    patches = dataclasses.replace(empty_patches, elevator_connection=elevator_connection)

    # Run
    result = patch_data_factory._create_elevators_field(patches, echoes_game_description)

    # Assert
    expected = [
        {"instance_id": 589851,
         "origin_location": {"world_asset_id": 1006255871, "area_asset_id": 2918020398},
         "target_location": {"world_asset_id": 464164546, "area_asset_id": 900285955},
         "room_name": "Transport to Sanctuary Spider side"},

        {"instance_id": 1572998,
         "origin_location": {"world_asset_id": 1006255871, "area_asset_id": 1660916974},
         "target_location": {"world_asset_id": 1039999561, "area_asset_id": 3479543630},
         "room_name": "Transport to Torvus Temple Access"},

        {"instance_id": 1966093,
         "origin_location": {"world_asset_id": 1006255871, "area_asset_id": 2889020216},
         "target_location": {"world_asset_id": 1039999561, "area_asset_id": 1868895730},
         "room_name": "Transport to Torvus Entrance"},

        {"instance_id": 2097251,
         "origin_location": {"world_asset_id": 1006255871, "area_asset_id": 1287880522},
         "target_location": {"world_asset_id": 2252328306, "area_asset_id": 2399252740},
         "room_name": "Transport to Temple Transport Violet"},

        {"instance_id": 136970379,
         "origin_location": {"world_asset_id": 1006255871, "area_asset_id": 2278776548},
         "target_location": {"world_asset_id": 2252328306,
                             "area_asset_id": 2068511343 if vanilla_gateway else 3619928121},
         "room_name": "Sky Temple Gateway" if vanilla_gateway else "Transport to Sanctum"},

        {"instance_id": 3342446,
         "origin_location": {"world_asset_id": 1006255871, "area_asset_id": 3455543403},
         "target_location": {"world_asset_id": 464164546, "area_asset_id": 3528156989},
         "room_name": "Transport to Sanctuary Entrance"},

        {"instance_id": 3538975,
         "origin_location": {"world_asset_id": 1006255871, "area_asset_id": 1345979968},
         "target_location": {"world_asset_id": 2252328306, "area_asset_id": 408633584},
         "room_name": "Transport to Temple Transport Emerald"},

        {"instance_id": 152,
         "origin_location": {"world_asset_id": 2252328306, "area_asset_id": 408633584},
         "target_location": {"world_asset_id": 1006255871, "area_asset_id": 1345979968},
         "room_name": "Transport to Sanctuary Quadrant"},

        {"instance_id": 393260,
         "origin_location": {"world_asset_id": 2252328306, "area_asset_id": 2556480432},
         "target_location": {"world_asset_id": 1006255871, "area_asset_id": 2918020398},
         "room_name": "Transport to Torvus Quadrant"},

        {"instance_id": 524321,
         "origin_location": {"world_asset_id": 2252328306, "area_asset_id": 2399252740},
         "target_location": {"world_asset_id": 1006255871, "area_asset_id": 1287880522},
         "room_name": "Transport to Agon Quadrant"},

        {'instance_id': 589949,
         'origin_location': {'area_asset_id': 2068511343, 'world_asset_id': 2252328306},
         'target_location': {'area_asset_id': 2278776548, 'world_asset_id': 1006255871},
         'room_name': 'Sky Temple Energy Controller'},

        {"instance_id": 122,
         "origin_location": {"world_asset_id": 1119434212, "area_asset_id": 1473133138},
         "target_location": {"world_asset_id": 1006255871, "area_asset_id": 1660916974},
         "room_name": "Transport to Agon Gate"},

        {"instance_id": 1245307,
         "origin_location": {"world_asset_id": 1119434212, "area_asset_id": 2806956034},
         "target_location": {"world_asset_id": 1039999561, "area_asset_id": 3479543630},
         "room_name": "Transport to Torvus Temple Access"},

        {"instance_id": 2949235,
         "origin_location": {"world_asset_id": 1119434212, "area_asset_id": 3331021649},
         "target_location": {"world_asset_id": 464164546, "area_asset_id": 900285955},
         "room_name": "Transport to Sanctuary Spider side"},

        {"instance_id": 129,
         "origin_location": {"world_asset_id": 1039999561, "area_asset_id": 1868895730},
         "target_location": {"world_asset_id": 1006255871, "area_asset_id": 2889020216},
         "room_name": "Transport to Torvus Gate"},

        {"instance_id": 2162826,
         "origin_location": {"world_asset_id": 1039999561, "area_asset_id": 3479543630},
         "target_location": {"world_asset_id": 1119434212, "area_asset_id": 2806956034},
         "room_name": "Transport to Agon Portal Access"},

        {"instance_id": 4522032,
         "origin_location": {"world_asset_id": 1039999561, "area_asset_id": 3205424168},
         "target_location": {"world_asset_id": 464164546, "area_asset_id": 3145160350},
         "room_name": "Transport to Sanctuary Vault side"},

        {"instance_id": 38,
         "origin_location": {"world_asset_id": 464164546, "area_asset_id": 3528156989},
         "target_location": {"world_asset_id": 1006255871, "area_asset_id": 3455543403},
         "room_name": "Transport to Sanctuary Gate"},

        {"instance_id": 1245332,
         "origin_location": {"world_asset_id": 464164546, "area_asset_id": 900285955},
         "target_location": {"world_asset_id": 1119434212, "area_asset_id": 3331021649},
         "room_name": "Transport to Agon Temple Access"},

        {"instance_id": 1638535,
         "origin_location": {"world_asset_id": 464164546, "area_asset_id": 3145160350},
         "target_location": {"world_asset_id": 1039999561, "area_asset_id": 3205424168},
         "room_name": "Transport to Lower Torvus Access"},

        {'instance_id': 204865660,
         'origin_location': {'world_asset_id': 464164546, 'area_asset_id': 3136899603},
         'target_location': {'world_asset_id': 464164546, 'area_asset_id': 1564082177},
         'room_name': 'Aerie Transport Station'},

        {'instance_id': 4260106,
         'origin_location': {'world_asset_id': 464164546, 'area_asset_id': 1564082177},
         'target_location': {'world_asset_id': 464164546, 'area_asset_id': 3136899603},
         'room_name': 'Aerie'}
    ]
    assert result == expected


def test_create_translator_gates_field(echoes_game_description):
    c = NodeIdentifier.create

    def make_req(item_id: int):
        return RequirementAnd([
            ResourceRequirement(
                ItemResourceInfo("Scan Visor", "Scan", 1, frozendict({"item_id": 9})), 1, False,
            ),
            ResourceRequirement(
                ItemResourceInfo("Other", "Other", 1, frozendict({"item_id": item_id})), 1, False,
            ),
        ])

    # Setup
    gate_assignment = {
        c("Temple Grounds", "Meeting Grounds", "Translator Gate"): make_req(0),
        c("Temple Grounds", "Industrial Site", "Translator Gate"): make_req(1),
        c("Temple Grounds", "Path of Eyes", "Translator Gate"): make_req(0),
    }

    # Run
    result = patch_data_factory._create_translator_gates_field(echoes_game_description, gate_assignment)

    # Assert
    assert result == [
        {"gate_index": 1, "translator_index": 0},
        {"gate_index": 3, "translator_index": 1},
        {"gate_index": 4, "translator_index": 0},
    ]


@pytest.mark.parametrize("elevators", [TeleporterShuffleMode.VANILLA, TeleporterShuffleMode.TWO_WAY_RANDOMIZED])
def test_apply_translator_gate_patches(elevators):
    # Setup
    target = {}

    # Run
    patch_data_factory._apply_translator_gate_patches(target, elevators)

    # Assert
    assert target == {
        "always_up_gfmc_compound": True,
        "always_up_torvus_temple": True,
        "always_up_great_temple": elevators != TeleporterShuffleMode.VANILLA,
    }


def test_get_single_hud_text_locked_pbs():
    # Run
    result = pickup_exporter._get_single_hud_text("Locked Power Bomb Expansion",
                                                  patch_data_factory._simplified_memo_data(),
                                                  tuple())

    # Assert
    assert result == "Power Bomb Expansion acquired, but the main Power Bomb is required to use it."


def test_pickup_data_for_seeker_launcher(echoes_item_database, echoes_resource_database):
    # Setup
    state = MajorItemState(
        include_copy_in_original_location=False,
        num_shuffled_pickups=0,
        num_included_in_starting_items=0,
        included_ammo=(5,),
    )
    pickup = pickup_creator.create_major_item(
        echoes_item_database.major_items["Seeker Launcher"],
        state,
        True,
        echoes_resource_database,
        echoes_item_database.ammo["Missile Expansion"],
        True
    )
    creator = pickup_exporter.PickupExporterSolo(patch_data_factory._simplified_memo_data())

    # Run
    details = creator.export(PickupIndex(0), PickupTarget(pickup, 0), pickup, PickupModelStyle.ALL_VISIBLE)
    result = patch_data_factory.echoes_pickup_details_to_patcher(details, MagicMock())

    # Assert
    assert result == {
        "pickup_index": 0,
        "scan": "Seeker Launcher",
        "model": {"game": "prime2", "name": "SeekerLauncher"},
        "hud_text": ["Seeker Launcher acquired, but the Missile Launcher is required to use it.",
                     "Seeker Launcher acquired!"],
        'resources': [{'amount': 5, 'index': 71},
                      {'amount': 1, 'index': 47},
                      {'amount': 1, 'index': 26}],
        "conditional_resources": [
            {'item': 73,
             'resources': [{'amount': 5, 'index': 44},
                           {'amount': 1, 'index': 47},
                           {'amount': 1, 'index': 26}]}
        ],
        "convert": [],
    }


@pytest.mark.parametrize("simplified", [False, True])
def test_pickup_data_for_pb_expansion_locked(simplified, echoes_item_database, echoes_resource_database):
    # Setup
    pickup = pickup_creator.create_ammo_expansion(
        echoes_item_database.ammo["Power Bomb Expansion"],
        [2],
        True,
        echoes_resource_database,
    )
    if simplified:
        memo = patch_data_factory._simplified_memo_data()
        hud_text = [
            "Power Bomb Expansion acquired, but the main Power Bomb is required to use it.",
            "Power Bomb Expansion acquired!",
        ]
    else:
        memo = default_database.default_prime2_memo_data()
        hud_text = [
            "Power Bomb Expansion acquired! \n"
            "Without the main Power Bomb item, you are still unable to release Power Bombs.",
            "Power Bomb Expansion acquired! \nMaximum Power Bomb carrying capacity increased by 2.",
        ]

    creator = pickup_exporter.PickupExporterSolo(memo)

    # Run
    details = creator.export(PickupIndex(0), PickupTarget(pickup, 0), pickup, PickupModelStyle.ALL_VISIBLE)
    result = patch_data_factory.echoes_pickup_details_to_patcher(details, MagicMock())

    # Assert
    assert result == {
        "pickup_index": 0,
        "scan": "Power Bomb Expansion. Provides 2 Power Bombs and 1 Item Percentage",
        "model": {"game": "prime2", "name": "PowerBombExpansion"},
        "hud_text": hud_text,
        'resources': [{'amount': 2, 'index': 72},
                      {'amount': 1, 'index': 47}],
        "conditional_resources": [
            {'item': 43,
             'resources': [{'amount': 2, 'index': 43},
                           {'amount': 1, 'index': 47}]}
        ],
        "convert": [],
    }


def test_pickup_data_for_pb_expansion_unlocked(echoes_item_database, echoes_resource_database):
    # Setup
    pickup = pickup_creator.create_ammo_expansion(
        echoes_item_database.ammo["Power Bomb Expansion"],
        [2],
        False,
        echoes_resource_database,
    )
    creator = pickup_exporter.PickupExporterSolo(patch_data_factory._simplified_memo_data())

    # Run
    details = creator.export(PickupIndex(0), PickupTarget(pickup, 0), pickup, PickupModelStyle.ALL_VISIBLE)
    result = patch_data_factory.echoes_pickup_details_to_patcher(details, MagicMock())

    # Assert
    assert result == {
        "pickup_index": 0,
        "scan": "Power Bomb Expansion. Provides 2 Power Bombs and 1 Item Percentage",
        "model": {"game": "prime2", "name": "PowerBombExpansion"},
        "hud_text": ["Power Bomb Expansion acquired!"],
        'resources': [{'amount': 2, 'index': 43},
                      {'amount': 1, 'index': 47}],
        "conditional_resources": [],
        "convert": [],
    }


@pytest.mark.parametrize("disable_hud_popup", [False, True])
def test_create_pickup_all_from_pool(echoes_resource_database,
                                     default_echoes_configuration,
                                     disable_hud_popup: bool
                                     ):
    item_pool = pool_creator.calculate_pool_results(default_echoes_configuration,
                                                    echoes_resource_database)
    index = PickupIndex(0)
    if disable_hud_popup:
        memo_data = patch_data_factory._simplified_memo_data()
    else:
        memo_data = default_prime2_memo_data()
    creator = pickup_exporter.PickupExporterSolo(memo_data)

    for item in item_pool.pickups:
        data = creator.export(index, PickupTarget(item, 0), item, PickupModelStyle.ALL_VISIBLE)
        for hud_text in data.hud_text:
            assert not hud_text.startswith("Locked")


def test_run_validated_hud_text():
    # Setup
    rng = MagicMock()
    rng.randint.return_value = 0
    details = pickup_exporter.ExportedPickupDetails(
        index=PickupIndex(0),
        scan_text="scan",
        hud_text=["Energy Transfer Module acquired!"],
        conditional_resources=[
            ConditionalResources(None, None, ()),
        ],
        conversion=[],
        model=PickupModel(
            game=RandovaniaGame.METROID_PRIME_ECHOES,
            name="EnergyTransferModule",
        ),
        other_player=False,
        original_pickup=None,
    )

    # Run
    data = patch_data_factory.echoes_pickup_details_to_patcher(details, rng)

    # Assert
    assert data['hud_text'] == ['Run validated!']


@pytest.mark.parametrize("stk_mode", SkyTempleKeyHintMode)
def test_create_string_patches(
        stk_mode: SkyTempleKeyHintMode,
        mocker,
):
    # Setup
    game = MagicMock()
    all_patches = MagicMock()
    rng = MagicMock()
    player_config = PlayersConfiguration(0, {0: "you"})

    mock_item_create_hints: MagicMock = mocker.patch(
        "randovania.games.prime2.exporter.hints.create_patches_hints",
        autospec=True, return_value=["item", "hints"],
    )
    mock_stk_create_hints: MagicMock = mocker.patch(
        "randovania.games.prime2.exporter.hints.create_stk_hints",
        autospec=True, return_value=["show", "hints"],
    )
    mock_stk_hide_hints: MagicMock = mocker.patch(
        "randovania.games.prime2.exporter.hints.hide_stk_hints",
        autospec=True, return_value=["hide", "hints"],
    )
    mock_logbook_title_string_patches: MagicMock = mocker.patch(
        "randovania.games.prime2.exporter.patch_data_factory._logbook_title_string_patches",
        autospec=True, return_values=[],
    )

    mock_akul_testament: MagicMock = mocker.patch(
        "randovania.games.prime2.exporter.patch_data_factory._akul_testament_string_patch",
        autospec=True,
    )
    mock_akul_testament.return_values = []
    namer = MagicMock()

    # Run
    result = patch_data_factory._create_string_patches(
        HintConfiguration(sky_temple_keys=stk_mode),
        game,
        all_patches,
        namer,
        player_config,
        rng,
    )

    # Assert
    expected_result = ["item", "hints"]
    mock_item_create_hints.assert_called_once_with(all_patches, player_config, game.world_list, namer, rng)
    mock_logbook_title_string_patches.assert_called_once_with()
    mock_akul_testament.assert_called_once_with(namer)

    if stk_mode == SkyTempleKeyHintMode.DISABLED:
        mock_stk_hide_hints.assert_called_once_with(namer)
        mock_stk_create_hints.assert_not_called()
        expected_result.extend(["hide", "hints"])

    else:
        mock_stk_create_hints.assert_called_once_with(all_patches, player_config, game.resource_database,
                                                      namer, stk_mode == SkyTempleKeyHintMode.HIDE_AREA)
        mock_stk_hide_hints.assert_not_called()
        expected_result.extend(["show", "hints"])

    assert result == expected_result


def test_generate_patcher_data(test_files_dir):
    # Setup
    description = LayoutDescription.from_file(test_files_dir.joinpath("log_files", "seed_a.rdvgame"))
    player_index = 0
    preset = description.get_preset(player_index)
    cosmetic_patches = EchoesCosmeticPatches()
    assert isinstance(preset.configuration, EchoesConfiguration)

    # Run
    result = patch_data_factory.generate_patcher_data(description, PlayersConfiguration(player_index, {0: "you"}),
                                                      cosmetic_patches)

    # Assert
    assert isinstance(result["spawn_point"], dict)

    assert isinstance(result["pickups"], list)
    assert len(result["pickups"]) == 119

    assert isinstance(result["elevators"], list)
    assert len(result["elevators"]) == 22

    assert isinstance(result["translator_gates"], list)
    assert len(result["translator_gates"]) == 17

    assert isinstance(result["string_patches"], list)
    assert len(result["string_patches"]) == 61

    assert result["specific_patches"] == {
        "hive_chamber_b_post_state": True,
        "intro_in_post_state": True,
        "warp_to_start": preset.configuration.warp_to_start,
        "credits_length": 75 if cosmetic_patches.speed_up_credits else 259,
        "disable_hud_popup": cosmetic_patches.disable_hud_popup,
        "pickup_map_icons": cosmetic_patches.pickup_markers,
        "full_map_at_start": cosmetic_patches.open_map,
        "dark_world_varia_suit_damage": preset.configuration.varia_suit_damage,
        "dark_world_dark_suit_damage": preset.configuration.dark_suit_damage,
        "always_up_gfmc_compound": True,
        "always_up_torvus_temple": True,
        "always_up_great_temple": False,
        'hud_color': None,
    }
    # TODO: check all fields?
    assert result["dol_patches"]["default_items"] == {
        "visor": "Combat Visor",
        "beam": "Power Beam",
    }
