"""Tests for performance optimization utilities."""

import pytest

from src.ui.performance import (
    StateChangeTracker,
    optimize_rerun,
    create_persona_lookup,
    PaginationHelper,
    BatchStateUpdate,
)
from src.models.persona import AIPersona


class TestStateChangeTracker:
    """Tests for StateChangeTracker class."""

    def test_initialization(self):
        """Test StateChangeTracker initializes correctly."""
        tracker = StateChangeTracker()
        assert len(tracker) == 0
        assert not tracker.has_changes()
        assert not bool(tracker)

    def test_adding_items(self):
        """Test adding items to tracker."""
        tracker = StateChangeTracker()
        tracker["key1"] = "value1"

        assert len(tracker) == 1
        assert tracker["key1"] == "value1"
        assert tracker.has_changes()
        assert bool(tracker)

    def test_multiple_items(self):
        """Test adding multiple items."""
        tracker = StateChangeTracker()
        tracker["personas"] = ["p1", "p2"]
        tracker["messages"] = ["m1", "m2", "m3"]
        tracker["config"] = {"setting": "value"}

        assert len(tracker) == 3
        assert tracker.has_changes()
        assert bool(tracker)
        assert "personas" in tracker
        assert "messages" in tracker
        assert "config" in tracker

    def test_boolean_context(self):
        """Test using tracker in boolean context."""
        tracker = StateChangeTracker()

        # Empty tracker should be falsy
        if tracker:
            pytest.fail("Empty tracker should be falsy")

        # Add item
        tracker["test"] = "value"

        # Tracker with changes should be truthy
        if not tracker:
            pytest.fail("Tracker with changes should be truthy")

    def test_dictionary_behavior(self):
        """Test that tracker behaves like a dictionary."""
        tracker = StateChangeTracker()
        tracker["a"] = 1
        tracker["b"] = 2
        tracker["c"] = 3

        assert list(tracker.keys()) == ["a", "b", "c"]
        assert list(tracker.values()) == [1, 2, 3]
        assert list(tracker.items()) == [("a", 1), ("b", 2), ("c", 3)]

        # Test get method
        assert tracker.get("a") == 1
        assert tracker.get("nonexistent") is None
        assert tracker.get("nonexistent", "default") == "default"


class TestOptimizeRerun:
    """Tests for optimize_rerun function."""

    def test_returns_state_change_tracker(self):
        """Test that optimize_rerun returns a StateChangeTracker."""
        result = optimize_rerun()
        assert isinstance(result, StateChangeTracker)
        assert isinstance(result, dict)

    def test_returned_tracker_is_empty(self):
        """Test that returned tracker starts empty."""
        tracker = optimize_rerun()
        assert len(tracker) == 0
        assert not tracker.has_changes()

    def test_can_track_changes(self):
        """Test that returned tracker can track changes."""
        changes = optimize_rerun()
        changes["test"] = "value"

        assert changes.has_changes()
        assert bool(changes)

    def test_use_case_from_docstring(self):
        """Test the use case shown in docstring."""
        changes = optimize_rerun()
        changes["personas"] = ["new_persona"]
        changes["messages"] = ["new_message"]

        # Should have changes
        assert changes
        assert len(changes) == 2

        # Should be able to check what changed
        if changes:
            assert "personas" in changes
            assert "messages" in changes


class TestCreatePersonaLookup:
    """Tests for create_persona_lookup function."""

    def test_empty_list(self):
        """Test with empty persona list."""
        lookup = create_persona_lookup([])
        assert lookup == {}

    def test_single_persona(self):
        """Test with single persona."""
        persona = AIPersona(
            id="1",
            name="Alice",
            model="llama2:latest",
            role="Philosopher",
            enabled=True
        )
        lookup = create_persona_lookup([persona])

        assert len(lookup) == 1
        assert "Alice" in lookup
        assert lookup["Alice"] == persona

    def test_multiple_personas(self):
        """Test with multiple personas."""
        personas = [
            AIPersona(id="1", name="Alice", model="llama2:latest", role="Philosopher", enabled=True),
            AIPersona(id="2", name="Bob", model="llama2:latest", role="Scientist", enabled=True),
            AIPersona(id="3", name="Charlie", model="llama2:latest", role="Artist", enabled=True),
        ]
        lookup = create_persona_lookup(personas)

        assert len(lookup) == 3
        assert "Alice" in lookup
        assert "Bob" in lookup
        assert "Charlie" in lookup
        assert lookup["Alice"].role == "Philosopher"
        assert lookup["Bob"].role == "Scientist"
        assert lookup["Charlie"].role == "Artist"


class TestPaginationHelper:
    """Tests for PaginationHelper class."""

    def test_initialization(self):
        """Test PaginationHelper initialization."""
        helper = PaginationHelper(items_per_page=50)
        assert helper.items_per_page == 50

        helper2 = PaginationHelper()
        assert helper2.items_per_page == 50  # default

    def test_get_total_pages(self):
        """Test calculating total pages."""
        helper = PaginationHelper(items_per_page=10)

        assert helper.get_total_pages([]) == 0
        assert helper.get_total_pages([1, 2, 3]) == 1
        assert helper.get_total_pages(list(range(10))) == 1
        assert helper.get_total_pages(list(range(11))) == 2
        assert helper.get_total_pages(list(range(25))) == 3
        assert helper.get_total_pages(list(range(100))) == 10

    def test_get_page_slice(self):
        """Test getting page slices."""
        helper = PaginationHelper(items_per_page=10)
        items = list(range(25))  # 0-24

        # Page 0
        slice_0, start_0, end_0 = helper.get_page_slice(items, page=0)
        assert slice_0 == list(range(10))
        assert start_0 == 0
        assert end_0 == 10

        # Page 1
        slice_1, start_1, end_1 = helper.get_page_slice(items, page=1)
        assert slice_1 == list(range(10, 20))
        assert start_1 == 10
        assert end_1 == 20

        # Page 2 (partial)
        slice_2, start_2, end_2 = helper.get_page_slice(items, page=2)
        assert slice_2 == list(range(20, 25))
        assert start_2 == 20
        assert end_2 == 25


class TestBatchStateUpdate:
    """Tests for BatchStateUpdate class."""

    def test_initialization(self):
        """Test BatchStateUpdate initialization."""
        batch = BatchStateUpdate()
        assert batch.updates == {}
        assert not batch.needs_rerun

    def test_update_method(self):
        """Test update method adds to updates dict."""
        batch = BatchStateUpdate()
        batch.update("key1", "value1")

        assert "key1" in batch.updates
        assert batch.updates["key1"] == "value1"
        assert batch.needs_rerun

    def test_multiple_updates(self):
        """Test multiple updates."""
        batch = BatchStateUpdate()
        batch.update("key1", "value1")
        batch.update("key2", "value2")
        batch.update("key3", "value3")

        assert len(batch.updates) == 3
        assert batch.needs_rerun


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
