import asyncio
from random import Random
import time
from typing import Callable, Tuple
from randovania.game_description import default_database
from randovania.game_description.assignment import DockWeaknessAssignment
from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo
from randovania.game_description.world.dock_node import DockNode
from randovania.game_description.world.node import NodeContext
from randovania.game_description.world.node_identifier import NodeIdentifier
from randovania.generator.filler.runner import FillerPlayerResult
from randovania.layout.base.base_configuration import BaseConfiguration
from randovania.layout.base.dock_rando_configuration import DockRandoMode
from randovania.resolver import debug, resolver
from randovania.resolver.logic import Logic
from randovania.resolver.resolver_reach import ResolverReach
from randovania.resolver.state import State


def distribute_pre_fill_weaknesses(patches: GamePatches):
    dock_rando = patches.configuration.dock_rando

    if dock_rando.mode == DockRandoMode.VANILLA:
        return patches
    
    game = default_database.game_description_for(patches.configuration.game)
    weakness_database = game.dock_weakness_database

    context = NodeContext(patches, patches.starting_items, game.resource_database, game.world_list)

    docks_to_unlock = {
        node.identifier: weakness_database.dock_rando_params[node.dock_type].unlocked
        for node in game.world_list.all_nodes
        if (
            isinstance(node, DockNode) and dock_rando.types_state[node.dock_type].can_shuffle
            and node.default_dock_weakness in dock_rando.types_state[node.dock_type].can_change_from
            and (
                dock_rando.mode == DockRandoMode.ONE_WAY or
                game.world_list.node_by_identifier(node.get_target_identifier(context)).default_dock_weakness in dock_rando.types_state[node.dock_type].can_change_from
            )
        )
    }

    return patches.assign_dock_weakness_assignment(docks_to_unlock)

    

class DockRandoLogic(Logic):
    dock: DockNode

    def __init__(self, game: GameDescription, configuration: BaseConfiguration, dock: DockNode):
        super().__init__(game, configuration)
        self.dock = dock
    
    @classmethod
    def from_logic(cls, logic: Logic, dock: DockNode) -> "DockRandoLogic":
        return cls(logic.game, logic.configuration, dock)

    def victory_condition_satisfied(self, state: State) -> bool:
        reach = ResolverReach.calculate_reach(self, state)
        return (
            self.dock in reach.nodes 
        )

RESOLVER_TIMEOUT = 0.5
async def distribute_post_fill_weaknesses(rng: Random,
                                    all_patches: dict[int, GamePatches],
                                    status_update: Callable[[str], None],
                                    ) -> dict[int, GamePatches]:
    """
    Distributes dock weaknesses using a modified assume fill algorithm
    """

    descriptions = {
        player: default_database.game_description_for(patches.configuration.game)
        for player, patches in all_patches.items()
    }

    unassigned_docks: list[Tuple[int, NodeIdentifier]] = []

    for player, patches in all_patches.items():
        if patches.configuration.dock_rando.mode != DockRandoMode.VANILLA:
            unassigned_docks.extend(((player, identifier) for identifier in patches.dock_weakness.keys()))
    
    rng.shuffle(unassigned_docks)

    docks_placed = 0
    docks_to_place = len(unassigned_docks)

    while unassigned_docks:
        await asyncio.sleep(0)
        status_update(f"{docks_placed}/{docks_to_place} docks placed")

        player, identifier = unassigned_docks.pop()

        game = descriptions[player]
        patches = all_patches[player]

        dock: DockNode = game.world_list.node_by_identifier(identifier)
        target: DockNode = game.world_list.node_by_identifier(dock.get_target_identifier(NodeContext(
            patches,
            patches.starting_items,
            game.resource_database,
            game.world_list,
        )))

        dock_type_params = game.dock_weakness_database.dock_rando_params[dock.dock_type]
        dock_type_state = patches.configuration.dock_rando.types_state[dock.dock_type]

        # Calculate the reach assuming this dock is completely locked
        locks = {identifier: dock_type_params.locked}
        if patches.configuration.dock_rando.mode == DockRandoMode.TWO_WAY:
            locks[target.identifier] = dock_type_params.locked
        locked_patches = patches.assign_dock_weakness_assignment(locks)

        state, logic = resolver.setup_resolver(patches.configuration, locked_patches)
        logic = DockRandoLogic.from_logic(logic, dock)
        debug.log_resolve_start()
        debug.debug_print(f"Starting {identifier} at {time.perf_counter()}")
        
        state_async = resolver.advance_depth(state, logic, lambda s: None)
        try:
            new_state = await asyncio.wait_for(state_async, RESOLVER_TIMEOUT)
        except asyncio.TimeoutError:
            new_state = None
            debug.debug_print("Timeout")
        else:
            debug.debug_print("Finished resolver")

        # Determine valid weaknesses to assign
        possible_weaknesses = [dock_type_params.unlocked]

        if new_state is not None:
            reach = ResolverReach.calculate_reach(logic, new_state)

            # FIXME: supposed to check if you can reach the target with the dock locked

            # if dock_type_params.locked in dock_type_state.can_change_to and target in reach.nodes:
            #     possible_weaknesses.append(dock_type_params.locked)
            
            debug.debug_print(f"{[res.long_name for res in new_state.resources if isinstance(res, (ItemResourceInfo, SimpleResourceInfo)) and res.resource_type in {ResourceType.ITEM, ResourceType.EVENT}]}")
            for weakness in dock_type_state.can_change_to.difference(possible_weaknesses):
                if weakness.requirement.satisfied(new_state.resources, new_state.energy, new_state.resource_database):
                    if weakness.lock is None or weakness.lock.requirement.satisfied(new_state.resources, new_state.energy, new_state.resource_database):
                        possible_weaknesses.append(weakness)
            
            pass
        
        # Assign the dock (and its target if desired/possible)
        new_assignment: DockWeaknessAssignment = {}

        weakness = rng.choice(possible_weaknesses)
        new_assignment[identifier] = weakness

        if patches.configuration.dock_rando.mode == DockRandoMode.TWO_WAY and (player, target) in unassigned_docks:
            unassigned_docks.remove((player, target))
            new_assignment[target] = weakness
        
        docks_placed += len(new_assignment.keys())
        debug.debug_print(f"{identifier}: {weakness} at {time.perf_counter()}")
        
        all_patches[player] = patches.assign_dock_weakness_assignment(new_assignment)
    
    return all_patches
