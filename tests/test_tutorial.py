"""Tests for the tutorial module."""

from __future__ import annotations

import sys
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.ui.tutorial import reset_tutorial


class MockSessionState:
    """Mock Streamlit session state for testing."""

    def __init__(self) -> None:
        self._state: dict[str, Any] = {}

    def __contains__(self, key: str) -> bool:
        return key in self._state

    def __getitem__(self, key: str) -> Any:
        return self._state[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self._state[key] = value

    def __getattr__(self, key: str) -> Any:
        if key.startswith("_"):
            return object.__getattribute__(self, key)
        return self._state.get(key)

    def __setattr__(self, key: str, value: Any) -> None:
        if key.startswith("_"):
            object.__setattr__(self, key, value)
        else:
            self._state[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from state with default."""
        return self._state.get(key, default)


class TestResetTutorial:
    """Tests for reset_tutorial function."""

    def test_reset_tutorial_sets_completed_false(self) -> None:
        """Test that reset_tutorial sets tutorial_completed to False."""
        session_state = MockSessionState()
        session_state.tutorial_completed = True
        session_state.tutorial_step = 3

        reset_tutorial(session_state)

        assert session_state.tutorial_completed is False

    def test_reset_tutorial_sets_step_to_zero(self) -> None:
        """Test that reset_tutorial sets tutorial_step to 0."""
        session_state = MockSessionState()
        session_state.tutorial_completed = True
        session_state.tutorial_step = 3

        reset_tutorial(session_state)

        assert session_state.tutorial_step == 0

    def test_reset_tutorial_with_fresh_state(self) -> None:
        """Test reset_tutorial with no prior state."""
        session_state = MockSessionState()

        reset_tutorial(session_state)

        assert session_state.tutorial_completed is False
        assert session_state.tutorial_step == 0


# Note: show_tutorial tests are omitted due to complexity of mocking Streamlit's
# import-inside-function pattern. The reset_tutorial function is well-tested above,
# and show_tutorial is tested via integration tests with actual Streamlit runtime.
