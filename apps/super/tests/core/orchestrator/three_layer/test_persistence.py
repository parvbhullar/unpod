"""Tests for SharedContext persistence adapter integration."""

from typing import Dict, List, Optional

import pytest

from super.core.orchestrator.three_layer.models import (
    ActionState,
    ActionStatus,
)
from super.core.orchestrator.three_layer.shared_context import (
    PersistenceAdapter,
    SharedContext,
)


class InMemoryAdapter:
    """In-memory implementation of PersistenceAdapter for testing."""

    def __init__(self) -> None:
        self._storage: Dict[str, ActionState] = {}

    async def save_action(self, action: ActionState) -> None:
        """Save action to in-memory storage (upsert behavior)."""
        self._storage[action["action_id"]] = action

    async def load_action(self, action_id: str) -> Optional[ActionState]:
        """Load action from in-memory storage."""
        return self._storage.get(action_id)

    async def load_thread_actions(self, thread_id: str) -> List[ActionState]:
        """Load all actions for a thread from in-memory storage."""
        return [
            action
            for action in self._storage.values()
            if action["thread_id"] == thread_id
        ]


class TestInMemoryAdapterProtocol:
    """Verify InMemoryAdapter implements PersistenceAdapter protocol."""

    def test_adapter_is_protocol_compliant(self) -> None:
        adapter = InMemoryAdapter()
        assert isinstance(adapter, PersistenceAdapter)


class TestPersistenceOnCreateAction:
    """Test that create_action persists to adapter."""

    @pytest.fixture
    def adapter(self) -> InMemoryAdapter:
        return InMemoryAdapter()

    @pytest.fixture
    def context_with_persistence(self, adapter: InMemoryAdapter) -> SharedContext:
        return SharedContext(persistence=adapter)

    @pytest.mark.anyio
    async def test_create_action_saves_to_adapter(
        self,
        adapter: InMemoryAdapter,
        context_with_persistence: SharedContext,
    ) -> None:
        action = await context_with_persistence.create_action(
            thread_id="thread-1",
            input_text="Test input",
        )

        persisted = await adapter.load_action(action["action_id"])
        assert persisted is not None
        assert persisted["action_id"] == action["action_id"]
        assert persisted["thread_id"] == "thread-1"
        assert persisted["input"] == "Test input"
        assert persisted["status"] == ActionStatus.PENDING

    @pytest.mark.anyio
    async def test_create_action_without_persistence_works(self) -> None:
        context = SharedContext()
        action = await context.create_action(
            thread_id="thread-1",
            input_text="Test input",
        )
        assert action["action_id"].startswith("act_")
        assert action["status"] == ActionStatus.PENDING


class TestPersistenceOnUpdateStatus:
    """Test that update_status persists to adapter."""

    @pytest.fixture
    def adapter(self) -> InMemoryAdapter:
        return InMemoryAdapter()

    @pytest.fixture
    def context_with_persistence(self, adapter: InMemoryAdapter) -> SharedContext:
        return SharedContext(persistence=adapter)

    @pytest.mark.anyio
    async def test_update_status_saves_to_adapter(
        self,
        adapter: InMemoryAdapter,
        context_with_persistence: SharedContext,
    ) -> None:
        action = await context_with_persistence.create_action(
            thread_id="thread-1",
            input_text="Test input",
        )

        await context_with_persistence.update_status(
            action["action_id"],
            ActionStatus.PROCESSING,
        )

        persisted = await adapter.load_action(action["action_id"])
        assert persisted is not None
        assert persisted["status"] == ActionStatus.PROCESSING

    @pytest.mark.anyio
    async def test_update_status_updates_timestamp(
        self,
        adapter: InMemoryAdapter,
        context_with_persistence: SharedContext,
    ) -> None:
        action = await context_with_persistence.create_action(
            thread_id="thread-1",
            input_text="Test input",
        )
        original_updated_at = action["updated_at"]

        await context_with_persistence.update_status(
            action["action_id"],
            ActionStatus.PROCESSING,
        )

        persisted = await adapter.load_action(action["action_id"])
        assert persisted is not None
        assert persisted["updated_at"] >= original_updated_at


class TestLoadThreadState:
    """Test that load_thread_state restores actions from adapter."""

    @pytest.fixture
    def adapter(self) -> InMemoryAdapter:
        return InMemoryAdapter()

    @pytest.mark.anyio
    async def test_load_thread_state_restores_actions(
        self,
        adapter: InMemoryAdapter,
    ) -> None:
        context1 = SharedContext(persistence=adapter)

        action1 = await context1.create_action(
            thread_id="thread-1",
            input_text="First action",
        )
        action2 = await context1.create_action(
            thread_id="thread-1",
            input_text="Second action",
        )
        await context1.update_status(action1["action_id"], ActionStatus.DONE)

        context2 = SharedContext(persistence=adapter)

        assert context2.get_action(action1["action_id"]) is None
        assert context2.get_action(action2["action_id"]) is None

        await context2.load_thread_state("thread-1")

        restored1 = context2.get_action(action1["action_id"])
        restored2 = context2.get_action(action2["action_id"])

        assert restored1 is not None
        assert restored1["input"] == "First action"
        assert restored1["status"] == ActionStatus.DONE

        assert restored2 is not None
        assert restored2["input"] == "Second action"
        assert restored2["status"] == ActionStatus.PENDING

    @pytest.mark.anyio
    async def test_load_thread_state_replaces_existing_actions(
        self,
        adapter: InMemoryAdapter,
    ) -> None:
        context1 = SharedContext(persistence=adapter)
        action = await context1.create_action(
            thread_id="thread-1",
            input_text="Original",
        )
        await context1.update_status(action["action_id"], ActionStatus.PROCESSING)

        context2 = SharedContext()
        local_action = await context2.create_action(
            thread_id="thread-1",
            input_text="Local only",
        )

        context2_with_persistence = SharedContext(persistence=adapter)
        context2_with_persistence._actions = context2._actions.copy()

        await context2_with_persistence.load_thread_state("thread-1")

        assert context2_with_persistence.get_action(local_action["action_id"]) is None

        restored = context2_with_persistence.get_action(action["action_id"])
        assert restored is not None
        assert restored["input"] == "Original"

    @pytest.mark.anyio
    async def test_load_thread_state_without_persistence_is_noop(self) -> None:
        context = SharedContext()
        await context.load_thread_state("thread-1")
        assert context.get_pending_actions("thread-1") == []

    @pytest.mark.anyio
    async def test_load_thread_state_only_loads_specified_thread(
        self,
        adapter: InMemoryAdapter,
    ) -> None:
        context1 = SharedContext(persistence=adapter)
        await context1.create_action(thread_id="thread-1", input_text="Thread 1")
        await context1.create_action(thread_id="thread-2", input_text="Thread 2")

        context2 = SharedContext(persistence=adapter)
        await context2.load_thread_state("thread-1")

        assert len(context2.get_pending_actions("thread-1")) == 1
        assert len(context2.get_pending_actions("thread-2")) == 0
