from __future__ import annotations

import asyncio
import time
import uuid
from unittest.mock import MagicMock

import pytest

from randovania.game.game_enum import RandovaniaGame
from randovania.game_connection.connector import abandoned_world_remote_connector
from randovania.game_connection.connector.abandoned_world_remote_connector import (
    AbandonedWorldRemoteConnector,
    setup_for_world,
)
from randovania.game_description.pickup.pickup_entry import PickupEntry
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.layout import game_patches_serializer
from randovania.layout.layout_description import LayoutDescription
from randovania.layout.versioned_preset import VersionedPreset
from randovania.network_common import error
from randovania.network_common.remote_pickup import RemotePickup
from randovania.resolver import debug


@pytest.fixture(scope="session")
def multi_layout(test_files_dir) -> LayoutDescription:
    return LayoutDescription.from_file(test_files_dir.joinpath("log_files", "prime1_and_2_multi.rdvgame"))


@pytest.fixture(scope="session")
def giant_multi_layout(test_files_dir) -> LayoutDescription:
    return LayoutDescription.from_file(
        test_files_dir.joinpath("log_files", "multi-am2r+cs+dread+prime1+prime2+msr.rdvgame")
    )


def make_connector(description: LayoutDescription, order: int) -> AbandonedWorldRemoteConnector:
    """A connector built from the same data the server serves for an abandoned world."""
    return AbandonedWorldRemoteConnector(
        uuid.uuid4(),
        VersionedPreset.with_preset(description.get_preset(order)),
        order,
        game_patches_serializer.serialize_single_world_only(
            order, len(description.all_patches), description.all_patches[order]
        ),
        [],
    )


def _collect_emissions_into(emitted: list[PickupIndex]):
    # a lambda, as RdvSignal only keeps a weak reference to plain functions and methods
    return lambda index: emitted.append(index)  # noqa: PLW0108


def is_idle(connector: AbandonedWorldRemoteConnector) -> bool:
    """
    The loop is parked waiting for items: nothing found by the last round and no inbound item since.

    The dirty flag is also briefly cleared while a round is being computed, but a poller can never
    observe that window with the faked rounds used here: the loop has no yield point between
    consuming the flag and either re-setting it or parking. Tests running the real resolver must
    additionally track in-flight rounds (see `tracked_rounds`).
    """
    return not connector._dirty.is_set()


async def wait_until(condition, timeout: float = 300.0) -> None:
    deadline = time.monotonic() + timeout
    while not condition():
        assert time.monotonic() < deadline, "timed out waiting for condition"
        await asyncio.sleep(0.01)


@pytest.fixture
def inert_loop(mocker):
    """Prevents the connector's background loop from resolving, for tests that drive rounds manually."""

    async def no_loop(self) -> None:
        pass

    mocker.patch.object(AbandonedWorldRemoteConnector, "_resolve_loop", no_loop)


@pytest.fixture
def instant_rounds(mocker):
    mocker.patch.object(AbandonedWorldRemoteConnector, "ROUND_DELAY_SECONDS", 0)


@pytest.fixture
def tracked_rounds(mocker):
    """Wraps the real `_resolve_one_round` to count rounds in flight, so tests running the real
    resolver can tell a parked loop apart from one still computing a round."""
    active = [0]
    original = AbandonedWorldRemoteConnector._resolve_one_round

    async def tracked(self):
        active[0] += 1
        try:
            return await original(self)
        finally:
            active[0] -= 1

    mocker.patch.object(AbandonedWorldRemoteConnector, "_resolve_one_round", tracked)

    def none_active() -> bool:
        return active[0] == 0

    return none_active


def fake_connector() -> AbandonedWorldRemoteConnector:
    """A connector with placeholder world data, for tests that fake the resolution rounds."""
    return AbandonedWorldRemoteConnector(uuid.uuid4(), MagicMock(), 0, {}, [])


@pytest.mark.usefixtures("inert_loop")
async def test_stops_when_world_no_longer_claimed():
    connector = fake_connector()
    await connector.on_world_sync_error(error.WorldNotAssociatedError())
    assert connector.is_disconnected()


@pytest.mark.usefixtures("inert_loop")
async def test_keeps_running_on_other_sync_errors():
    connector = fake_connector()
    try:
        await connector.on_world_sync_error(error.ServerError())
        assert not connector.is_disconnected()
    finally:
        await connector.force_finish()


async def test_loop_resolves_goes_idle_and_wakes_on_items(mocker, instant_rounds):
    # The per-world cycle: one round per cycle while rounds keep finding locations; an empty round
    # goes idle; an item arriving from another world wakes it up and re-checks.
    rounds = [({1, 2}, None), ({3}, None), (set(), None), ({4}, None), (set(), None)]
    calls: list[int] = []

    async def fake_round(self):
        result = rounds[len(calls)]
        calls.append(1)
        return result

    mocker.patch.object(AbandonedWorldRemoteConnector, "_resolve_one_round", fake_round)

    connector = fake_connector()
    emitted: list[PickupIndex] = []
    connector.PickupIndexCollected.connect(_collect_emissions_into(emitted))
    try:
        await wait_until(lambda: is_idle(connector), timeout=10)
        assert len(calls) == 3, "two productive rounds, then the empty round that goes idle"
        assert connector.collected_locations == {1, 2, 3}
        assert emitted == [PickupIndex(1), PickupIndex(2), PickupIndex(3)]

        # An inbound item wakes the connector up; it finds one more location and goes idle again.
        await connector.set_remote_pickups((RemotePickup("Other World", MagicMock(spec=PickupEntry), None),))
        assert not is_idle(connector)

        await wait_until(lambda: is_idle(connector), timeout=10)
        assert len(calls) == 5
        assert connector.collected_locations == {1, 2, 3, 4}
        assert emitted == [PickupIndex(1), PickupIndex(2), PickupIndex(3), PickupIndex(4)]
    finally:
        await connector.force_finish()
    assert connector.is_disconnected()


async def test_loop_never_resolvable_stays_idle(mocker, instant_rounds):
    # A world locked behind items that never arrive: every check finds nothing, and the connector
    # only ever re-checks when an item actually arrives.
    calls: list[int] = []

    async def fake_round(self):
        calls.append(1)
        return set(), None

    mocker.patch.object(AbandonedWorldRemoteConnector, "_resolve_one_round", fake_round)

    connector = fake_connector()
    emitted: list[PickupIndex] = []
    connector.PickupIndexCollected.connect(_collect_emissions_into(emitted))
    try:
        await wait_until(lambda: is_idle(connector), timeout=10)
        assert len(calls) == 1

        # An item that unlocks nothing: one more check, then idle again. No spinning in between.
        await connector.set_remote_pickups((RemotePickup("Other World", MagicMock(spec=PickupEntry), None),))
        await wait_until(lambda: is_idle(connector), timeout=10)
        assert len(calls) == 2
        assert connector.collected_locations == frozenset()
        assert emitted == []
    finally:
        await connector.force_finish()


async def test_set_remote_pickups_seeds_own_collections(inert_loop):
    # Pickups the world provided to itself (recorded server-side) mark their location as collected
    # instead of being granted twice: collecting the node already grants its pickup.
    connector = fake_connector()
    own_pickup = MagicMock(spec=PickupEntry)
    other_pickup = MagicMock(spec=PickupEntry)

    await connector.set_remote_pickups(
        (
            RemotePickup("This World", own_pickup, PickupIndex(5)),
            RemotePickup("Other World", other_pickup, None),
        )
    )

    assert connector.collected_locations == {5}
    assert connector._received_pickups == [other_pickup]


async def test_setup_grants_only_self_pickups(multi_layout):
    # The stripped payload must produce the same logic as the full patches: pickup nodes grant
    # exactly the world's own pickups, and pickups owned by other worlds never leak in.
    order = 0
    description = multi_layout
    modifications = game_patches_serializer.serialize_single_world_only(
        order, len(description.all_patches), description.all_patches[order]
    )
    graph, _ = setup_for_world(description.get_preset(order).configuration, modifications, order)

    full_assignment = description.all_patches[order].pickup_assignment
    checked_self = 0
    for pickup_index, node in graph.node_by_pickup_index.items():
        target = full_assignment.get(pickup_index)
        if target is not None and target.player == order:
            assert node.pickup_entry is not None
            assert node.pickup_entry.name == target.pickup.name
            checked_self += 1
        else:
            assert node.pickup_entry is None
    assert checked_self > 0, "expected the world to hold some of its own pickups"


async def test_resolve_loop_real_world(multi_layout, instant_rounds, tracked_rounds):
    # End-to-end with the real resolver: the connector drains everything in logic, goes idle since
    # the rest is locked behind items other worlds still hold, then resumes when those arrive.
    connector = make_connector(multi_layout, 0)
    emitted: list[PickupIndex] = []
    connector.PickupIndexCollected.connect(_collect_emissions_into(emitted))

    try:
        await wait_until(lambda: is_idle(connector) and tracked_rounds())
        first_pass = set(connector.collected_locations)
        assert first_pass, "the abandoned world should collect the locations in logic from a fresh start"
        assert {index.index for index in emitted} == first_pass

        assert connector._graph is not None
        all_locations = {pickup_index.index for pickup_index in connector._graph.node_by_pickup_index}
        assert first_pass < all_locations, "some locations must be locked behind other worlds' items"

        # Deliver everything the other world holds for this one.
        held_for_world = [
            target.pickup for _, target in multi_layout.all_patches[1].pickup_assignment.items() if target.player == 0
        ]
        assert held_for_world
        await connector.set_remote_pickups(tuple(RemotePickup("World 2", pickup, None) for pickup in held_for_world))

        await wait_until(lambda: is_idle(connector) and tracked_rounds())
        assert set(connector.collected_locations) > first_pass, "received items must unlock more locations"
        assert {index.index for index in emitted} == set(connector.collected_locations)
    finally:
        await connector.force_finish()


async def test_connectors_share_no_mutable_state(multi_layout, inert_loop):
    # Two connectors for the same world, resolving concurrently: they must be fully independent, so
    # progress applied to one may not leak into the other.
    connector_a = make_connector(multi_layout, 0)
    connector_b = make_connector(multi_layout, 0)

    with debug.with_level(debug.LogLevel.SILENT):
        (result_a, _), (result_b, _) = await asyncio.gather(
            connector_a._resolve_one_round(), connector_b._resolve_one_round()
        )

    assert result_a
    assert result_a == result_b, "same inputs must give the same result"
    assert connector_a._graph is not connector_b._graph
    assert connector_a._starting_state is not connector_b._starting_state

    # Applying progress to one connector must not affect the other.
    connector_a._collected.update(result_a)
    assert connector_b.collected_locations == frozenset()
    (result_b2, _) = await connector_b._resolve_one_round()
    assert result_b2 == result_b


# @pytest.mark.skip_resolver_tests
@pytest.mark.skip
async def test_dread_abandoned_in_giant_multi_is_monotonic(giant_multi_layout):
    # Abandon the Dread world of a 6-game multiworld, then deliver it the pickups other worlds hold
    # for it in increasing amounts, checking at each step that the in-logic set never shrinks.
    # Dread's one-way geometry and dangerous events are what stress the resolver-driven strategy, so
    # this exercises exactly that. Deliberately slow (several resolver sweeps over a full Dread world).

    description = giant_multi_layout
    dread_order = next(
        order
        for order in range(len(description.all_patches))
        if description.get_preset(order).game == RandovaniaGame.METROID_DREAD
    )

    configuration = description.get_preset(dread_order).configuration
    modifications = game_patches_serializer.serialize_single_world_only(
        dread_order, len(description.all_patches), description.all_patches[dread_order]
    )
    # One setup shared across all rounds, exactly like a connector reuses its own graph.
    graph, starting_state = setup_for_world(configuration, modifications, dread_order)

    # The pickups other worlds hold for Dread, in a deterministic order.
    held_for_dread = sorted(
        (
            (provider, pickup_index.index, target.pickup)
            for provider in range(len(description.all_patches))
            if provider != dread_order
            for pickup_index, target in description.all_patches[provider].pickup_assignment.items()
            if target.player == dread_order
        ),
        key=lambda entry: (entry[0], entry[1]),
    )
    assert len(held_for_dread) > 100, "expected the giant multi to spread most of Dread's items around"

    self_collected: set[int] = set()
    for received_items in [0, 20, 60, 100, len(held_for_dread)]:
        received = [pickup for _, _, pickup in held_for_dread[:received_items]]
        while True:
            start = time.perf_counter()
            with debug.with_level(debug.LogLevel.SILENT):
                new_pickup, _ = await abandoned_world_remote_connector._compute_one_round(
                    graph, starting_state, configuration, set(self_collected), received
                )
            elapsed = time.perf_counter() - start
            if new_pickup:
                self_collected = self_collected.union(new_pickup)
            print(f"received count={received_items}: {len(self_collected)} locations in logic, took {elapsed:.2f}s,")
            if not new_pickup:
                break
