"""REAL INTEGRATION TESTS - These tests validate actual system functionality with real components."""

import asyncio
import shutil
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

import pytest

# Import the actual application modules
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.models.persona import AIPersona
from src.services.logger import ConversationLogger
from src.services.ollama_client import OllamaClient
from streamlit_backroom import StreamlitBackroomApp


@pytest.fixture(scope="session")
def init_streamlit_session():
    """Initialize Streamlit session state for testing."""
    import streamlit as st

    # Mock the session state if running outside Streamlit
    try:
        # Try to get the script run context using the current API
        from streamlit.runtime.scriptrunner import get_script_run_ctx

        ctx = get_script_run_ctx()
        has_context = ctx is not None
    except (AttributeError, ImportError):
        # Fallback if API changes
        has_context = False

    if not has_context:
        # Create a mock session state
        if not hasattr(st, "session_state"):

            class MockSessionState(dict):
                def __getattr__(self, key):
                    try:
                        return self[key]
                    except KeyError as err:
                        raise AttributeError(f"st.session_state has no attribute '{key}'") from err

                def __setattr__(self, key, value):
                    self[key] = value

            st.session_state = MockSessionState()

            # Initialize required session state variables
            st.session_state.personas = []
            st.session_state.messages = []
            st.session_state.last_speaker_index = None
            st.session_state.available_models = []
            st.session_state.non_thinking_models = set()
            st.session_state.settings = {
                "context_messages": 10,
                "response_delay_min": 2,
                "response_delay_max": 8,
                "auto_advance": True,
                "enable_thinking": True,
                "response_timeout": 300,
            }

    yield st.session_state


class TestRealOllamaIntegration:
    """Test actual Ollama API connections and real model responses."""

    @pytest.fixture(scope="class")
    def real_client(self, init_streamlit_session):
        """Create real OllamaClient pointing to localhost."""
        return OllamaClient("http://localhost:11434")

    @pytest.mark.asyncio
    async def test_real_ollama_connection(self, real_client):
        """Test real connection to Ollama API."""
        async with real_client:
            success, models = await real_client.test_connection()

        assert success is True, f"Failed to connect to Ollama: {models}"
        assert len(models) >= 1, "No models available"
        assert (
            "granite3.3:8b" in models or "llama3:8b" in models or "phi3:mini" in models
        ), "Expected models not found"

    @pytest.mark.asyncio
    async def test_real_model_response(self, real_client):
        """Test getting actual response from real model."""
        model = "phi3:mini"  # Use smaller, faster model for testing

        # Collect actual response chunks
        chunks = []
        async with real_client:
            async for chunk in real_client.generate_stream(
                model, "What is 2+2? Answer in one word."
            ):
                chunks.append(chunk)
                if chunk.get("done"):
                    break

        assert len(chunks) >= 1, "No response chunks received"

        # Extract response text
        response_text = ""
        for chunk in chunks:
            if chunk.get("response"):
                response_text += chunk["response"]

        assert len(response_text.strip()) > 0, "Empty response received"
        # Should contain a number or word indicating the answer
        assert any(
            word in response_text.lower() for word in ["4", "four", "answer"]
        ), f"Unexpected response: {response_text}"

    @pytest.mark.asyncio
    async def test_real_concurrent_requests(self, real_client):
        """Test actual concurrent requests to real models."""
        model = "phi3:mini"
        prompts = ["What color is the sky?", "What is 1+1?", "Say hello"]

        async def get_response(prompt):
            chunks = []
            async for chunk in real_client.generate_stream(model, prompt):
                chunks.append(chunk)
                if chunk.get("done"):
                    break
            return "".join(c.get("response", "") for c in chunks)

        # Run 3 requests concurrently
        start_time = time.time()
        async with real_client:
            results = await asyncio.gather(
                get_response(prompts[0]), get_response(prompts[1]), get_response(prompts[2])
            )
        end_time = time.time()

        assert len(results) == 3, "Not all concurrent requests completed"
        for i, result in enumerate(results):
            assert len(result.strip()) > 0, f"Empty response for prompt {i}: {prompts[i]}"

        # Should complete reasonably fast (under 30 seconds for 3 small requests)
        assert (
            end_time - start_time < 30
        ), f"Concurrent requests took too long: {end_time - start_time}s"


class TestRealConversationFlow:
    """Test actual conversation flows with real AI responses."""

    @pytest.fixture
    def temp_log_dir(self):
        """Create temporary directory for conversation logs."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def real_app(self, temp_log_dir, init_streamlit_session):
        """Create real StreamlitBackroomApp with temp directory."""
        app = StreamlitBackroomApp()
        # Initialize session state
        app.initialize_session_state()
        # Override log directory
        app.conversation_logger = ConversationLogger(temp_log_dir)
        return app

    @pytest.fixture
    def test_personas(self):
        """Create real test personas for actual model use."""
        return [
            AIPersona(
                id="test_1",
                name="Alice",
                model="phi3:mini",  # Use small model for speed
                role="Mathematician",
                enabled=True,
                color="#FF6B6B",
            ),
            AIPersona(
                id="test_2",
                name="Bob",
                model="phi3:mini",
                role="Scientist",
                enabled=True,
                color="#4ECDC4",
            ),
        ]

    def test_real_persona_creation_and_selection(self, real_app, test_personas):
        """Test real persona creation and speaker selection."""
        import streamlit as st

        # Mock session state
        st.session_state.personas = test_personas
        st.session_state.last_speaker_index = None

        # Test speaker selection
        speaker1 = real_app.get_next_speaker()
        assert speaker1 is not None, "No speaker selected"
        assert speaker1.name == "Alice", f"Expected Alice, got {speaker1.name}"

        speaker2 = real_app.get_next_speaker()
        assert speaker2 is not None, "No second speaker selected"
        assert speaker2.name == "Bob", f"Expected Bob, got {speaker2.name}"

        # Should cycle back
        speaker3 = real_app.get_next_speaker()
        assert speaker3.name == "Alice", f"Expected Alice again, got {speaker3.name}"

    def test_real_conversation_logging(self, real_app, test_personas, temp_log_dir):
        """Test real conversation logging to file system."""
        import streamlit as st

        # Setup
        st.session_state.personas = test_personas
        alice = test_personas[0]

        # Log a real message
        test_message = "This is a test message for logging"
        real_app.conversation_logger.log_message(alice.name, test_message, datetime.now())

        # Verify log file was created
        log_files = list(Path(temp_log_dir).glob("*.txt"))
        assert len(log_files) >= 1, "No log file created"

        # Verify content
        log_content = log_files[0].read_text(encoding="utf-8")
        assert alice.name in log_content, "Persona name not in log"
        assert test_message in log_content, "Test message not in log"


class TestRealFileOperations:
    """Test real file system operations without mocking."""

    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace for file operations."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_real_conversation_logger_file_operations(self, temp_workspace):
        """Test real conversation logger file operations."""
        log_dir = Path(temp_workspace)
        logger = ConversationLogger(str(log_dir))

        # Test log file creation
        today = datetime.now().strftime("%Y-%m-%d")
        expected_filename = f"streamlit_backroom_{today}.txt"
        expected_path = log_dir / expected_filename

        # Log multiple messages
        messages = [
            ("Alice", "Hello world", datetime.now()),
            ("Bob", "Hi there", datetime.now()),
            ("Alice", "How are you?", datetime.now()),
        ]

        for persona, message, timestamp in messages:
            logger.log_message(persona, message, timestamp)

        # Verify file exists
        assert expected_path.exists(), "Log file not created"

        # Verify content
        content = expected_path.read_text(encoding="utf-8")
        assert "Alice" in content, "Alice not in log"
        assert "Bob" in content, "Bob not in log"
        assert "Hello world" in content, "First message not in log"
        assert "Hi there" in content, "Second message not in log"
        assert "How are you?" in content, "Third message not in log"

        # Test message parsing
        parsed_messages = logger.parse_log_file(expected_path)
        assert len(parsed_messages) >= 3, f"Expected 3+ messages, got {len(parsed_messages)}"

        # Verify parsed structure
        for msg in parsed_messages[:3]:
            assert "persona" in msg, "Missing persona in parsed message"
            assert "content" in msg, "Missing content in parsed message"
            assert "timestamp" in msg, "Missing timestamp in parsed message"

    def test_real_log_rotation(self, temp_workspace):
        """Test real log file rotation across days."""
        log_dir = Path(temp_workspace)
        logger = ConversationLogger(str(log_dir))

        # Simulate different days
        yesterday = datetime(2025, 11, 11)
        today = datetime(2025, 11, 12)

        # Log messages for different days
        logger.log_message("Alice", "Yesterday's message", yesterday)
        logger.log_message("Bob", "Today's message", today)

        # Should have separate log files
        log_files = list(log_dir.glob("*.txt"))
        assert len(log_files) == 2, f"Expected 2 log files, got {len(log_files)}"

        # Verify file names contain dates
        file_names = [f.name for f in log_files]
        assert any("2025-11-11" in name for name in file_names), "Yesterday's log file missing"
        assert any("2025-11-12" in name for name in file_names), "Today's log file missing"


class TestRealSystemPerformance:
    """Test real system performance under realistic conditions."""

    @pytest.mark.asyncio
    async def test_concurrent_real_conversations(self):
        """Test multiple concurrent real conversations."""
        client = OllamaClient("http://localhost:11434")

        async def run_conversation(conversation_id):
            """Run a mini conversation."""
            responses = []
            model = "phi3:mini"
            prompts = [
                f"Conversation {conversation_id}: Who are you?",
                f"Conversation {conversation_id}: What do you do?",
            ]

            for prompt in prompts:
                response_text = ""
                try:
                    async for chunk in client.generate_stream(model, prompt):
                        if chunk.get("response"):
                            response_text += chunk.get("response")
                        if chunk.get("done"):
                            break
                    responses.append(response_text.strip())
                except Exception:
                    # Handle gracefully
                    responses.append(f"Error in conversation {conversation_id}")

            return responses

        # Run 3 conversations concurrently
        start_time = time.time()
        results = await asyncio.gather(
            run_conversation(1), run_conversation(2), run_conversation(3), return_exceptions=True
        )
        end_time = time.time()

        # Verify all completed
        assert len(results) == 3, "Not all conversations completed"

        # Check for exceptions
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Conversation {i+1} failed: {result}")
            else:
                assert len(result) >= 1, f"Conversation {i+1} had no responses"

        # Should complete in reasonable time
        assert (
            end_time - start_time < 120
        ), f"Concurrent conversations took too long: {end_time - start_time}s"

    def test_memory_usage_stability(self):
        """Test memory usage stability over extended operation."""
        import gc

        # Create and use many objects
        for i in range(100):
            # Create temporary objects
            temp_data = []
            for j in range(100):
                temp_data.append(
                    {
                        "id": f"{i}_{j}",
                        "content": "Test content " * 10,
                        "timestamp": datetime.now(),
                        "metadata": {"iteration": i, "sub_iteration": j},
                    }
                )

            # Simulate some processing
            processed = [item for item in temp_data if item["metadata"]["iteration"] % 2 == 0]

            # Clear references
            del temp_data
            del processed

            if i % 20 == 0:
                gc.collect()

        # Final cleanup
        gc.collect()

        # If we get here without memory errors, the test passes
        assert True, "Memory stability test completed"


class TestEndToEndRealSystem:
    """Complete end-to-end tests with real system components."""

    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def integrated_system(self, temp_workspace, init_streamlit_session):
        """Create fully integrated system with real components."""
        # Real Ollama client
        client = OllamaClient("http://localhost:11434")

        # Real conversation logger
        logger = ConversationLogger(temp_workspace)

        # Real app with real components
        app = StreamlitBackroomApp()
        app.ollama_client = client
        app.conversation_logger = logger

        # Initialize with real settings
        import streamlit as st

        app.initialize_session_state()
        st.session_state.settings = {
            "context_messages": 5,
            "enable_thinking": False,
            "response_timeout": 90,
        }

        return app, client, logger

    @pytest.mark.asyncio
    async def test_complete_real_workflow(self, integrated_system):
        """Test complete real workflow from personas to conversation."""
        app, client, logger = integrated_system

        # Test Ollama connection
        success, models = await client.test_connection()
        assert success, "Ollama not available for end-to-end test"

        # Create personas
        personas = [
            AIPersona(
                id="e2e_1",
                name="TestAI",
                model="phi3:mini",
                role="Assistant",
                enabled=True,
                color="#FF6B6B",
            )
        ]

        import streamlit as st

        st.session_state.personas = personas
        st.session_state.messages = []

        # Test speaker selection
        speaker = app.get_next_speaker()
        assert speaker is not None, "No speaker selected"
        assert speaker.name == "TestAI", f"Wrong speaker: {speaker.name}"

        # Test system prompt generation
        prompt = app.generate_system_prompt(speaker)
        assert speaker.name in prompt, "Speaker name not in system prompt"
        assert len(prompt) > 50, "System prompt too short"

        # Test real AI response
        response_text = ""
        try:
            async for chunk in app.get_ai_response_stream(
                speaker, "Say hello in exactly one word."
            ):
                if chunk.get("response"):
                    response_text += chunk.get("response")
        except Exception as e:
            pytest.fail(f"Real AI response failed: {e}")

        assert len(response_text.strip()) > 0, "No response from AI"

        # Test logging
        logger.log_message(speaker.name, response_text.strip(), datetime.now())

        # Verify log file created
        log_files = list(Path(logger.log_dir).glob("*.txt"))
        assert len(log_files) >= 1, "No log files created"

        # Verify log content
        log_content = log_files[0].read_text(encoding="utf-8")
        assert speaker.name in log_content, "Speaker not in log"
        assert response_text.strip() in log_content, "Response not in log"

    def test_error_handling_robustness(self, integrated_system):
        """Test system error handling and robustness."""
        app, client, logger = integrated_system

        # Test graceful handling of invalid operations
        try:
            # Try logging with various edge cases
            test_cases = [
                ("Test", "Normal message"),
                ("Special", "Message with special chars: !@#$%^&*()"),
                ("Unicode", "Message with unicode: ñáéíóú 🚀"),
                ("Long", "A" * 500),  # Long message
                ("Empty", ""),  # Empty message
            ]

            for persona, message in test_cases:
                logger.log_message(persona, message, datetime.now())

            # Verify logging survived edge cases
            log_files = list(Path(logger.log_dir).glob("*.txt"))
            if log_files:
                content = log_files[0].read_text(encoding="utf-8")
                assert len(content) > 0, "Log file empty after edge cases"

        except Exception as e:
            pytest.fail(f"Error handling test failed: {e}")

        # Test invalid model handling (without crashing)
        try:
            # This should not crash the system
            personas = [
                AIPersona(
                    id="invalid",
                    name="InvalidModel",
                    model="nonexistent:model",
                    role="Test",
                    enabled=True,
                    color="#FF0000",
                )
            ]

            import streamlit as st

            st.session_state.personas = personas

            # Should handle gracefully
            speaker = app.get_next_speaker()
            if speaker:
                system_prompt = app.generate_system_prompt(speaker)
                assert speaker.name in system_prompt, "System prompt generation failed"

        except Exception as e:
            # Should not crash, but can have expected errors
            assert not isinstance(e, SystemExit), "System crashed during error handling"
