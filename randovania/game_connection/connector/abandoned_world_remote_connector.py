"""
RemoteConnector that plays an "abandoned" multiworld world like a bot: it collects the locations in
logic for the world, freeing the items it holds for other players, and keeps up as it receives more
items.

This connector drives the world with the resolver. It works in *paced rounds*: each
round finds one more reachable location, then waits ``ROUND_DELAY_SECONDS`` before the next round.
Once a round finds nothing new, the connector goes idle and only re-checks when it receives something
new through ``set_remote_pickups``.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import time
from typing import TYPE_CHECKING

from randovania.game_connection.connector.remote_connector import PlayerLocationEvent, RemoteConnector
from randovania.game_description.resources.inventory import Inventory
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.generator.pickup_pool import pool_creator
from randovania.graph.graph_requirement import GraphRequirementList, GraphRequirementSet
from randovania.layout import filtered_database, game_patches_serializer
from randovania.network_common.error import WorldNotAssociatedError
from randovania.resolver import debug
from randovania.resolver.exceptions import ResolverTimeoutError
from randovania.resolver.logic import Logic
from randovania.resolver.resolver import advance_depth

if TYPE_CHECKING:
    import uuid
    from collections.abc import Iterable

    from randovania.game.game_enum import RandovaniaGame
    from randovania.game_description.pickup.pickup_entry import PickupEntry
    from randovania.graph.state import State
    from randovania.graph.world_graph import WorldGraph
    from randovania.layout.base.base_configuration import BaseConfiguration
    from randovania.layout.versioned_preset import VersionedPreset
    from randovania.network_common.error import BaseNetworkError
    from randovania.network_common.remote_pickup import RemotePickup

# Runaway guard: cap resolver attempts per round. Hitting it treats the world as exhausted for now;
# the next delivery re-triggers it, so a briefly-uncollected location is only delayed, never wrong.
_MAX_RESOLVER_ATTEMPTS = 500_000

logger = logging.getLogger(__name__)


def setup_for_world(configuration: BaseConfiguration, game_modifications: dict, order: int) -> tuple[WorldGraph, State]:
    """
    Builds the world graph and starting state for one world (same as ``resolver.setup_resolver``)
    from the data served by the server for an abandoned world.

    ``game_modifications`` is the world's entry of a ``game_patches_serializer`` payload, with the
    pickups owned by other worlds already stripped by the server -- the graph only ever grants
    self-owned pickups (items for other worlds don't affect this world's logic), so the resolution
    is identical to one over the full patches.
    """
    immutable_game = filtered_database.game_description_for_layout(configuration)
    pool = pool_creator.calculate_pool_results(configuration, immutable_game)
    patches = game_patches_serializer.decode_single(
        order, {order: pool}, immutable_game, game_modifications, configuration, {order: immutable_game}
    )

    game = immutable_game.get_mutable()
    bootstrap = game.game.generator.bootstrap
    game.resource_database = bootstrap.patch_resource_database(game.resource_database, configuration)
    graph, starting_state = bootstrap.logic_bootstrap_graph(configuration, game, patches)
    return graph, starting_state


class _AbandonedWorldLogic(Logic):
    """
    Logic whose victory condition is "collect any location not already in ``collected``".

    Each pickup node grants a unique node-resource when collected, so "collected location L" becomes
    "require L's node-resource"
    """

    def __init__(self, graph: WorldGraph, configuration: BaseConfiguration, collected: set[int]):
        super().__init__(graph, configuration, disable_gc=False)

        resource_database = graph.converter.resource_database
        victory = GraphRequirementSet()
        for pickup_index, node in graph.node_by_pickup_index.items():
            if pickup_index.index in collected:
                continue
            alternative = GraphRequirementList(resource_database)
            alternative.add_resource(graph.resource_info_for_node(node), 1, False)
            victory.add_alternative(alternative)
        victory.freeze()
        self._victory_condition = victory


def _fresh_state(
    graph: WorldGraph, starting_state: State, collected: set[int], received_pickups: list[PickupEntry]
) -> State:
    """
    A fresh start state: player at the start node, holding the already-collected locations and the
    received pickups.

    Collecting the already-collected nodes grants their resources (the permanent inventory the player
    keeps) and marks them collected, so the resolver won't re-collect them.
    """
    state = starting_state.copy()
    for index in collected:
        node = graph.node_by_pickup_index.get(PickupIndex(index))
        if node is not None:
            state = state.collect_resource_node(node, state.damage_state)
    return state.assign_pickups_resources(received_pickups)


async def _compute_one_round(
    graph: WorldGraph,
    starting_state: State,
    configuration: BaseConfiguration,
    collected: set[int],
    received_pickups: list[PickupEntry],
) -> tuple[set[int], State | None]:
    """
    One resolver step: find and collect a single uncollected reachable location.
    Returns the newly-collected pickup indices (empty if nothing more is reachable) and the state the
    resolver ended in, for inventory reporting.
    """
    logic = _AbandonedWorldLogic(graph, configuration, collected)
    state = _fresh_state(graph, starting_state, collected, received_pickups)
    if logic.victory_condition(state).num_alternatives() == 0:
        return set(), state  # every location collected; an empty OR would force a pointless full sweep

    try:
        result = await advance_depth(state, logic, lambda s: None, max_attempts=_MAX_RESOLVER_ATTEMPTS)
    except ResolverTimeoutError:
        logger.info("Abandoned world connector paused; will retry when new items arrive.")
        logger.debug("Resolver attempt cap reached (%d).", _MAX_RESOLVER_ATTEMPTS)
        return set(), state
    if result is None:
        return set(), state  # nothing new reachable

    return {pickup_index.index for pickup_index in result.collected_pickup_indices(graph)} - collected, result


class AbandonedWorldRemoteConnector(RemoteConnector):
    """Plays an abandoned world by resolving it, one paced round at a time. See the module docstring."""

    # Pause between rounds while the world keeps yielding locations. Bounds the resolver to one round
    # per this window, keeping the GUI responsive even with many abandoned world remote connector running.
    ROUND_DELAY_SECONDS: float = 10.0

    remote_pickups: tuple[RemotePickup, ...] = ()

    def __init__(
        self,
        layout_uuid: uuid.UUID,
        preset: VersionedPreset,
        order: int,
        game_modifications: dict,
        collected_locations: Iterable[int],
    ):
        super().__init__()
        self._layout_uuid = layout_uuid
        self._preset = preset
        self._order = order
        self._game_modifications = game_modifications

        # All mutable resolution state is owned by this connector instance.
        self._collected: set[int] = set(collected_locations)
        self._received_pickups: list[PickupEntry] = []
        self._graph: WorldGraph | None = None
        self._starting_state: State | None = None
        self._last_inventory_event = Inventory.empty()

        self._finished = False
        # "Dirty" flag: the world must be re-checked. Starts set so attaching always resumes from
        # wherever the world stopped; cleared when a round finds nothing, set again by inbound items.
        self._dirty = asyncio.Event()
        self._dirty.set()
        self._task = asyncio.create_task(self._resolve_loop())

    @property
    def game_enum(self) -> RandovaniaGame:
        return self._preset.game

    def description(self) -> str:
        return f"Abandoned world bot - {self.game_enum.long_name}"

    @property
    def collected_locations(self) -> frozenset[int]:
        """All locations this connector knows to be collected."""
        return frozenset(self._collected)

    async def set_remote_pickups(self, remote_pickups: tuple[RemotePickup, ...]) -> None:
        self.remote_pickups = remote_pickups

        received = []
        for remote_pickup in remote_pickups:
            # server is recording local pickups for an abandoned world.
            # because their receiver is this world, it has the coop_location flag set.
            if remote_pickup.coop_location is not None:
                self._collected.add(remote_pickup.coop_location.index)
            else:
                received.append(remote_pickup.pickup_entry)
        self._received_pickups = received

        # An item arrived (or our record changed): wake up and re-check what is in logic now.
        self._dirty.set()

    async def on_world_sync_error(self, err: BaseNetworkError) -> None:
        if isinstance(err, WorldNotAssociatedError):
            logger.info("No longer claiming world %s; stopping its bot.", self._layout_uuid)
            await self.force_finish()

    async def force_finish(self) -> None:
        self._finished = True
        self._dirty.set()  # unblock the loop so it can exit
        if not self._task.done():
            self._task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await self._task

    def is_disconnected(self) -> bool:
        return self._finished

    def _ensure_setup(self) -> tuple[WorldGraph, State]:
        if self._graph is None or self._starting_state is None:
            self._graph, self._starting_state = setup_for_world(
                self._preset.get_preset().configuration, self._game_modifications, self._order
            )
        return self._graph, self._starting_state

    async def _resolve_one_round(self) -> tuple[set[int], State | None]:
        graph, starting_state = self._ensure_setup()
        configuration = self._preset.get_preset().configuration
        with debug.with_level(debug.LogLevel.SILENT):
            return await _compute_one_round(
                graph, starting_state, configuration, set(self._collected), list(self._received_pickups)
            )

    async def _resolve_loop(self) -> None:
        """
        Drives the world: while dirty, collect one round per cycle, paced; once a round finds nothing,
        go idle until ``set_remote_pickups`` receives something new.
        """
        try:
            emitted_location = False
            while not self._finished:
                await self._dirty.wait()
                self._dirty.clear()
                if self._finished:
                    return

                start = time.perf_counter()
                new_indices, end_state = await self._resolve_one_round()
                elapsed = time.perf_counter() - start
                if elapsed > 1.0:
                    logger.info(
                        "Round for world %s took %.2fs, collected %d locations",
                        self._layout_uuid,
                        elapsed,
                        len(new_indices),
                    )

                if not emitted_location and end_state is not None:
                    # Report being "in-game" at the starting node, so the world counts as connected.
                    emitted_location = True
                    self.PlayerLocationChanged.emit(PlayerLocationEvent(end_state.node.region, end_state.node.area))

                self._emit_inventory(end_state)

                if new_indices:
                    self._collected.update(new_indices)
                    for index in sorted(new_indices):
                        self.PickupIndexCollected.emit(PickupIndex(index))

                    # More may be in logic: stay scheduled for the next paced round.
                    self._dirty.set()
                    await asyncio.sleep(self.ROUND_DELAY_SECONDS)
                # else: nothing new this round. The dirty flag stays cleared, so the loop parks at
                # the top until an item arriving from another world sets it again.

        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Abandoned world connector for %s failed; disconnecting it.", self._layout_uuid)
            self._finished = True

    def _emit_inventory(self, state: State | None) -> None:
        if state is None:
            return
        new_inventory = Inventory.from_collection(state.resources)
        if self._last_inventory_event != new_inventory:
            self._last_inventory_event = new_inventory
            self.InventoryUpdated.emit(new_inventory)
