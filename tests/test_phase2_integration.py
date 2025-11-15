"""Integration tests for Phase 2 modular architecture.

Tests the interaction between all refactored modules and ensures
the main application works correctly with the new architecture.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import asyncio
import tempfile
import json
from pathlib import Path

from streamlit_backroom_refactored import StreamlitBackroomApp
from src.state.session_manager import SecureSessionManager
from src.services.conversation_orchestrator import ConversationOrchestrator
from src.services.logger import ConversationLogger
from src.ui.conversation_ui import ConversationUI
from src.ui.persona_manager import PersonaManager
from src.ui.settings_manager import SettingsManager
from src.ui.export_manager import ExportManager
from src.models.persona import AIPersona


class TestPhase2Integration:
    """Integration tests for the refactored modular architecture."""

    @pytest.fixture
    def temp_log_dir(self):
        """Create temporary directory for test logs."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def mock_streamlit(self):
        """Mock all Streamlit components for testing."""
        with patch('streamlit.set_page_config'), \
             patch('streamlit.session_state', {}), \
             patch('streamlit.sidebar'), \
             patch('streamlit.columns'), \
             patch('streamlit.tabs'), \
             patch('streamlit.subheader'), \
             patch('streamlit.info'), \
             patch('streamlit.warning'), \
             patch('streamlit.error'), \
             patch('streamlit.success'), \
             patch('streamlit.caption'), \
             patch('streamlit.image'), \
             patch('streamlit.metric'), \
             patch('streamlit.divider'), \
             patch('streamlit.markdown'):
            yield

    @pytest.fixture
    def sample_personas(self):
        """Create sample personas for testing."""
        return [
            AIPersona(
                name="Alice",
                model="llama2",
                description="AI expert in machine learning",
                role="Expert",
                thinking_enabled=True,
                enabled=True
            ),
            AIPersona(
                name="Bob",
                model="mistral",
                description="Creative AI assistant",
                role="Creative",
                thinking_enabled=False,
                enabled=True
            )
        ]

    @pytest.fixture
    def app_with_mocks(self, temp_log_dir):
        """Create application instance with mocked dependencies."""
        # Create real components
        session_manager = SecureSessionManager()
        conversation_logger = ConversationLogger(log_dir=temp_log_dir)
        conversation_orchestrator = ConversationOrchestrator(
            session_manager=session_manager,
            conversation_logger=conversation_logger
        )

        # Mock the Ollama client in orchestrator
        with patch('src.services.conversation_orchestrator.OptimizedOllamaClient'):
            # Create UI managers
            conversation_ui = ConversationUI(
                session_manager=session_manager,
                conversation_orchestrator=conversation_orchestrator
            )
            persona_manager = PersonaManager(session_manager)
            settings_manager = SettingsManager(session_manager)
            export_manager = ExportManager(
                session_manager=session_manager,
                conversation_logger=conversation_logger
            )

            # Create app instance with mocked Ollama client
            with patch('streamlit_backroom_refactored.PerformanceTimer'):
                app = StreamlitBackroomApp()
                app.session_manager = session_manager
                app.conversation_logger = conversation_logger
                app.conversation_orchestrator = conversation_orchestrator
                app.conversation_ui = conversation_ui
                app.persona_manager = persona_manager
                app.settings_manager = settings_manager
                app.export_manager = export_manager

                yield app

    def test_app_initialization(self, app_with_mocks):
        """Test application initialization creates all required components."""
        app = app_with_mocks

        # Verify all components are created
        assert app.session_manager is not None
        assert app.conversation_logger is not None
        assert app.conversation_orchestrator is not None
        assert app.conversation_ui is not None
        assert app.persona_manager is not None
        assert app.settings_manager is not None
        assert app.export_manager is not None

        # Verify components are properly linked
        assert app.conversation_ui.session_manager == app.session_manager
        assert app.persona_manager.session_manager == app.session_manager
        assert app.settings_manager.session_manager == app.session_manager
        assert app.export_manager.session_manager == app.session_manager

    def test_session_initialization(self, app_with_mocks):
        """Test session initialization works correctly."""
        app = app_with_mocks

        # Initialize session
        app.initialize_session()

        # Verify session state is set up
        assert hasattr(app.session_manager, 'session_id')
        assert app.session_manager.session_id is not None

        # Check default settings are applied
        personas = app.session_manager.get_personas()
        assert isinstance(personas, list)

    def test_persona_manager_integration(
        self, app_with_mocks, sample_personas, mock_streamlit
    ):
        """Test persona manager integration with session manager."""
        app = app_with_mocks

        # Add personas to session manager
        for persona in sample_personas:
            app.session_manager.add_persona(persona)

        # Verify personas are available
        personas = app.session_manager.get_personas()
        assert len(personas) == 2

        # Test persona manager can access personas
        enabled_personas = app.session_manager.get_enabled_personas()
        assert len(enabled_personas) == 2

        # Test filtering through persona manager
        filtered = app.persona_manager._filter_personas(
            personas, show_enabled=True, show_disabled=False
        )
        assert len(filtered) == 2

    def test_settings_manager_integration(self, app_with_mocks, mock_streamlit):
        """Test settings manager integration with session manager."""
        app = app_with_mocks

        # Test setting and getting values
        app.session_manager.set_setting("test_setting", "test_value")
        value = app.session_manager.get_setting("test_setting")
        assert value == "test_value"

        # Test default value
        default_value = app.session_manager.get_setting("nonexistent_setting", "default")
        assert default_value == "default"

        # Test settings summary
        summary = app.settings_manager.get_setting_summary()
        assert isinstance(summary, dict)
        assert "auto_advance" in summary
        assert "thinking_enabled" in summary

    def test_export_manager_integration(
        self, app_with_mocks, sample_personas, mock_streamlit
    ):
        """Test export manager integration with session and conversation logger."""
        app = app_with_mocks

        # Add personas and messages
        for persona in sample_personas:
            app.session_manager.add_persona(persona)

        # Add some test messages
        test_message = {
            "role": "assistant",
            "content": "Test message from Alice",
            "persona_name": "Alice",
            "timestamp": "2025-01-14T12:00:00"
        }
        app.session_manager.add_message(test_message)

        # Test export functionality
        messages = app.session_manager.get_messages()
        assert len(messages) == 1

        # Test word frequency calculation
        word_freq = app.export_manager._calculate_word_frequency(messages)
        assert isinstance(word_freq, list)

        # Test persona statistics
        persona_stats = app.export_manager._calculate_persona_statistics(messages)
        assert isinstance(persona_stats, dict)

    def test_conversation_orchestrator_integration(
        self, app_with_mocks, sample_personas
    ):
        """Test conversation orchestrator integration."""
        app = app_with_mocks

        # Add personas
        for persona in sample_personas:
            app.session_manager.add_persona(persona)

        # Test system prompt generation
        persona = app.session_manager.get_enabled_personas()[0]
        system_prompt = app.conversation_orchestrator.generate_system_prompt(persona)
        assert isinstance(system_prompt, str)
        assert persona.name in system_prompt

        # Test conversation prompt generation
        conversation_prompt = app.conversation_orchestrator.generate_conversation_prompt(persona)
        assert isinstance(conversation_prompt, str)

        # Test conversation statistics
        stats = app.conversation_orchestrator.get_conversation_stats()
        assert isinstance(stats, dict)
        assert "enabled_persona_names" in stats

    def test_conversation_ui_integration(self, app_with_mocks, mock_streamlit):
        """Test conversation UI integration."""
        app = app_with_mocks

        # Mock Streamlit components for UI rendering
        with patch('streamlit.chat_input') as mock_chat_input, \
             patch('streamlit.chat_message') as mock_chat_message, \
             patch('streamlit.form') as mock_form, \
             patch('streamlit.form_submit_button') as mock_form_submit:

            # Test conversation interface rendering
            app.conversation_ui.render_conversation_interface()

            # Verify UI components were called
            mock_chat_input.assert_called()

    @patch('streamlit_backroom_refactored.safe_async_call')
    def test_ollama_connection_check(self, mock_safe_async, app_with_mocks):
        """Test Ollama connection checking."""
        app = app_with_mocks

        # Mock successful connection
        mock_safe_async.return_value = True

        # Test connection check
        result = app.check_ollama_connection()

        # Verify async call was made
        mock_safe_async.assert_called_once()
        assert result is True

    @patch('streamlit_backroom_refactored.safe_async_call')
    def test_ollama_connection_check_failure(self, mock_safe_async, app_with_mocks):
        """Test Ollama connection check failure."""
        app = app_with_mocks

        # Mock failed connection
        mock_safe_async.return_value = False

        # Test connection check
        result = app.check_ollama_connection()

        # Verify async call was made
        mock_safe_async.assert_called_once()
        assert result is False

    def test_error_handling(self, app_with_mocks, mock_streamlit):
        """Test error handling in application."""
        app = app_with_mocks

        # Test handling of exceptions
        test_error = ValueError("Test error message")

        with patch('streamlit.error') as mock_error:
            app.handle_error(test_error, "test context")

            # Should show error message
            mock_error.assert_called()

    def test_error_handling_debug_mode(self, app_with_mocks, mock_streamlit):
        """Test error handling in debug mode."""
        app = app_with_mocks

        # Enable debug mode
        app.session_manager.set_setting("debug_mode", True)

        test_error = ValueError("Test error message")

        with patch('streamlit.error') as mock_error, \
             patch('streamlit.code') as mock_code:

            app.handle_error(test_error, "test context")

            # Should show error and code
            mock_error.assert_called()
            mock_code.assert_called()

    def test_application_workflow(self, app_with_mocks, sample_personas, mock_streamlit):
        """Test complete application workflow."""
        app = app_with_mocks

        # Initialize session
        app.initialize_session()

        # Add personas
        for persona in sample_personas:
            app.session_manager.add_persona(persona)

        # Configure settings
        app.session_manager.set_setting("auto_advance", True)
        app.session_manager.set_setting("context_messages", 15)

        # Add conversation messages
        messages = [
            {
                "role": "user",
                "content": "Hello, how are you?",
                "timestamp": "2025-01-14T12:00:00"
            },
            {
                "role": "assistant",
                "content": "I'm doing well, thank you!",
                "persona_name": "Alice",
                "model": "llama2",
                "timestamp": "2025-01-14T12:00:05"
            }
        ]

        for message in messages:
            app.session_manager.add_message(message)

        # Verify workflow state
        personas = app.session_manager.get_personas()
        assert len(personas) == 2

        messages = app.session_manager.get_messages()
        assert len(messages) == 2

        settings = app.session_manager.get_all_settings()
        assert settings["auto_advance"] is True
        assert settings["context_messages"] == 15

        # Test conversation orchestrator with current state
        enabled_personas = app.session_manager.get_enabled_personas()
        assert len(enabled_personas) == 2

        stats = app.conversation_orchestrator.get_conversation_stats()
        assert stats["total_message_count"] == 2
        assert len(stats["enabled_persona_names"]) == 2

    def test_module_interaction_dependencies(self, app_with_mocks):
        """Test that modules interact correctly with their dependencies."""
        app = app_with_mocks

        # Test that persona manager uses session manager correctly
        assert app.persona_manager.session_manager == app.session_manager

        # Test that settings manager uses session manager correctly
        assert app.settings_manager.session_manager == app.session_manager

        # Test that export manager uses both session manager and logger
        assert app.export_manager.session_manager == app.session_manager
        assert app.export_manager.conversation_logger == app.conversation_logger

        # Test that conversation UI uses correct dependencies
        assert app.conversation_ui.session_manager == app.session_manager
        assert app.conversation_ui.conversation_orchestrator == app.conversation_orchestrator

    def test_memory_usage_and_cleanup(self, app_with_mocks):
        """Test that components properly manage memory and cleanup resources."""
        app = app_with_mocks

        # Add data to components
        for i in range(100):
            app.session_manager.set_setting(f"test_setting_{i}", f"test_value_{i}")

        # Verify data exists
        settings = app.session_manager.get_all_settings()
        assert len(settings) >= 100

        # Test session cleanup
        app.session_manager.clear_conversation()

        # Verify conversation data is cleared but settings remain
        messages = app.session_manager.get_messages()
        assert len(messages) == 0

        settings_after_cleanup = app.session_manager.get_all_settings()
        assert len(settings_after_cleanup) >= 100

    @patch('streamlit_backroom_refactored.cleanup_thread_resources')
    def test_application_cleanup(self, mock_cleanup, app_with_mocks):
        """Test application cleanup procedures."""
        app = app_with_mocks

        # Test cleanup during shutdown
        from streamlit_backroom_refactored import initialize_application_state

        initialize_application_state()

        # Verify cleanup was called
        mock_cleanup.assert_called()

    def test_configuration_loading(self, app_with_mocks):
        """Test configuration loading and default values."""
        app = app_with_mocks

        # Test default configuration values
        auto_advance = app.session_manager.get_setting("auto_advance", False)
        thinking_enabled = app.session_manager.get_setting("enable_thinking", False)
        context_messages = app.session_manager.get_setting("context_messages", 10)

        # These should have default values
        assert isinstance(auto_advance, bool)
        assert isinstance(thinking_enabled, bool)
        assert isinstance(context_messages, int)
        assert context_messages > 0

    def test_state_persistence(self, app_with_mocks):
        """Test that application state persists correctly."""
        app = app_with_mocks

        # Set some state
        app.session_manager.set_setting("test_key", "test_value")
        test_persona = AIPersona(
            name="StateTest",
            model="llama2",
            description="State test persona",
            enabled=True
        )
        app.session_manager.add_persona(test_persona)

        # Verify state exists
        assert app.session_manager.get_setting("test_key") == "test_value"
        personas = app.session_manager.get_personas()
        assert len(personas) == 1
        assert personas[0].name == "StateTest"

        # Test state retrieval through different managers
        settings_summary = app.settings_manager.get_setting_summary()
        assert "test_key" in app.session_manager.get_all_settings()

        enabled_personas = app.session_manager.get_enabled_personas()
        assert len(enabled_personas) == 1
        assert enabled_personas[0].name == "StateTest"


class TestPhase2Performance:
    """Performance tests for the refactored architecture."""

    @pytest.fixture
    def app_with_mocks(self):
        """Create application instance for performance testing."""
        session_manager = SecureSessionManager()
        conversation_logger = ConversationLogger()

        with patch('src.services.conversation_orchestrator.OptimizedOllamaClient'):
            conversation_orchestrator = ConversationOrchestrator(
                session_manager=session_manager,
                conversation_logger=conversation_logger
            )

            conversation_ui = ConversationUI(
                session_manager=session_manager,
                conversation_orchestrator=conversation_orchestrator
            )
            persona_manager = PersonaManager(session_manager)
            settings_manager = SettingsManager(session_manager)
            export_manager = ExportManager(
                session_manager=session_manager,
                conversation_logger=conversation_logger
            )

            with patch('streamlit_backroom_refactored.PerformanceTimer'):
                app = StreamlitBackroomApp()
                app.session_manager = session_manager
                app.conversation_logger = conversation_logger
                app.conversation_orchestrator = conversation_orchestrator
                app.conversation_ui = conversation_ui
                app.persona_manager = persona_manager
                app.settings_manager = settings_manager
                app.export_manager = export_manager

                yield app

    def test_initialization_performance(self, app_with_mocks):
        """Test application initialization performance."""
        import time

        start_time = time.time()

        # Initialize application
        app_with_mocks.initialize_session()

        init_time = time.time() - start_time

        # Initialization should be fast (< 100ms)
        assert init_time < 0.1, f"Initialization took {init_time:.3f}s, expected < 0.1s"

    def test_persona_operations_performance(self, app_with_mocks):
        """Test persona CRUD operations performance."""
        import time

        # Test persona creation performance
        start_time = time.time()

        personas = []
        for i in range(100):
            persona = AIPersona(
                name=f"PerfTest_{i}",
                model="llama2",
                description=f"Performance test persona {i}",
                enabled=i % 2 == 0
            )
            personas.append(persona)
            app_with_mocks.session_manager.add_persona(persona)

        creation_time = time.time() - start_time

        # Creating 100 personas should be fast (< 1s)
        assert creation_time < 1.0, f"Creating 100 personas took {creation_time:.3f}s"

        # Test retrieval performance
        start_time = time.time()

        retrieved_personas = app_with_mocks.session_manager.get_personas()
        enabled_personas = app_with_mocks.session_manager.get_enabled_personas()

        retrieval_time = time.time() - start_time

        # Retrieval should be very fast (< 10ms)
        assert retrieval_time < 0.01, f"Retrieving personas took {retrieval_time:.3f}s"
        assert len(retrieved_personas) == 100
        assert len(enabled_personas) == 50

    def test_settings_operations_performance(self, app_with_mocks):
        """Test settings operations performance."""
        import time

        # Test bulk settings operations
        start_time = time.time()

        for i in range(1000):
            app_with_mocks.session_manager.set_setting(f"perf_test_{i}", f"value_{i}")

        settings_time = time.time() - start_time

        # Setting 1000 values should be fast (< 100ms)
        assert settings_time < 0.1, f"Setting 1000 values took {settings_time:.3f}s"

        # Test retrieval performance
        start_time = time.time()

        for i in range(1000):
            value = app_with_mocks.session_manager.get_setting(f"perf_test_{i}")
            assert value == f"value_{i}"

        retrieval_time = time.time() - start_time

        # Retrieving 1000 values should be fast (< 50ms)
        assert retrieval_time < 0.05, f"Retrieving 1000 values took {retrieval_time:.3f}s"

    def test_memory_usage_scaling(self, app_with_mocks):
        """Test that memory usage scales reasonably with data size."""
        import psutil
        import os

        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Add large amount of data
        large_messages = []
        for i in range(1000):
            large_message = {
                "role": "assistant",
                "content": "Large message content " + "x" * 1000,  # 1KB per message
                "persona_name": f"PerfBot_{i % 10}",
                "timestamp": f"2025-01-14T12:{i:02d}:00"
            }
            large_messages.append(large_message)
            app_with_mocks.session_manager.add_message(large_message)

        # Check memory usage after adding data
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (< 50MB for 1000 messages)
        assert memory_increase < 50 * 1024 * 1024, f"Memory increase was {memory_increase / 1024 / 1024:.1f}MB, expected < 50MB"

        # Verify data integrity
        messages = app_with_mocks.session_manager.get_messages()
        assert len(messages) == 1000

        # Cleanup test data
        app_with_mocks.session_manager.clear_conversation()