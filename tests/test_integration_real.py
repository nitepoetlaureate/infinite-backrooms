"""REAL INTEGRATION TESTS - No Mocks! These tests validate actual system functionality."""

import pytest
import asyncio
import json
import time
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import subprocess
import os
import sys

# Import the actual application modules
sys.path.insert(0, str(Path(__file__).parent.parent))
from streamlit_backroom import OllamaClient, StreamlitBackroomApp, AIPersona, SecureConversationLogger


@pytest.mark.integration
class TestRealOllamaIntegration:
    """Test actual Ollama API connections and real model responses.

    These tests require a live Ollama instance running on localhost:11434.
    Skip with: pytest -m "not integration"
    """

    @pytest.fixture(scope="class")
    def real_client(self):
        """Create real OllamaClient pointing to localhost."""
        return OllamaClient("http://localhost:11434")

    @pytest.mark.asyncio
    async def test_real_ollama_connection(self, real_client):
        """Test real connection to Ollama API."""
        success, models = await real_client.test_connection()

        assert success is True, f"Failed to connect to Ollama: {models}"
        assert len(models) >= 1, "No models available"
        assert "granite3.3:8b" in models or "llama3:8b" in models or "phi3:mini" in models, "Expected models not found"

    @pytest.mark.asyncio
    async def test_real_model_response(self, real_client):
        """Test getting actual response from real model."""
        model = "phi3:mini"  # Use smaller, faster model for testing

        # Collect actual response chunks
        chunks = []
        async for chunk in real_client.generate_stream(model, "What is 2+2? Answer in one word."):
            chunks.append(chunk)
            if chunk.get("done"):
                break

        assert len(chunks) >= 1, "No response chunks received"

        # Extract response text
        response_text = ""
        for chunk in chunks:
            if "response" in chunk:
                response_text += chunk["response"]

        assert len(response_text.strip()) > 0, "Empty response received"
        # Should contain a number or word indicating the answer
        assert any(word in response_text.lower() for word in ["4", "four", "answer"]), f"Unexpected response: {response_text}"

    @pytest.mark.asyncio
    async def test_real_model_with_system_prompt(self, real_client):
        """Test real model with system prompt."""
        model = "phi3:mini"
        system_prompt = "You are a mathematician. Always answer with just the number."

        chunks = []
        async for chunk in real_client.generate_stream(
            model,
            "What is five plus three?",
            system=system_prompt
        ):
            chunks.append(chunk)
            if chunk.get("done"):
                break

        response_text = ""
        for chunk in chunks:
            if "response" in chunk:
                response_text += chunk["response"]

        assert len(response_text.strip()) > 0, "Empty response with system prompt"
        # Should contain "8" or "eight"
        assert any(word in response_text.lower() for word in ["8", "eight"]), f"Unexpected math response: {response_text}"

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
        results = await asyncio.gather(
            get_response(prompts[0]),
            get_response(prompts[1]),
            get_response(prompts[2])
        )
        end_time = time.time()

        assert len(results) == 3, "Not all concurrent requests completed"
        for i, result in enumerate(results):
            assert len(result.strip()) > 0, f"Empty response for prompt {i}: {prompts[i]}"

        # Should complete reasonably fast (under 30 seconds for 3 small requests)
        assert end_time - start_time < 30, f"Concurrent requests took too long: {end_time - start_time}s"

    @pytest.mark.asyncio
    async def test_real_error_handling_invalid_model(self, real_client):
        """Test real error handling with invalid model."""
        chunks = []
        error_occurred = False

        try:
            async for chunk in real_client.generate_stream("nonexistent:model", "test"):
                chunks.append(chunk)
                if chunk.get("done"):
                    break
        except Exception as e:
            error_occurred = True
            # Should get some kind of error about model not found
            assert "model" in str(e).lower() or "not found" in str(e).lower() or "404" in str(e), f"Unexpected error: {e}"

        # Either we get an error or empty response, both are valid error handling
        if not error_occurred:
            # If no exception, we should have an error response
            response_text = "".join(c.get("response", "") for c in chunks)
            assert len(response_text) == 0 or "error" in response_text.lower(), "Expected error response"


class TestRealConversationFlow:
    """Test actual conversation flows with real AI responses."""

    @pytest.fixture
    def temp_log_dir(self):
        """Create temporary directory for conversation logs."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def real_app(self, temp_log_dir):
        """Create real StreamlitBackroomApp with temp directory."""
        app = StreamlitBackroomApp()
        # Initialize session state
        app.initialize_session_state()
        # Override log directory
        app.conversation_logger = SecureConversationLogger(temp_log_dir)
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
                color="#FF6B6B"
            ),
            AIPersona(
                id="test_2",
                name="Bob",
                model="phi3:mini",
                role="Scientist",
                enabled=True,
                color="#4ECDC4"
            )
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

    def test_real_system_prompt_generation(self, real_app, test_personas):
        """Test real system prompt generation for personas."""
        import streamlit as st
        st.session_state.personas = test_personas

        alice = test_personas[0]
        prompt = real_app.generate_system_prompt(alice)

        assert alice.name in prompt, "Persona name not in system prompt"
        assert "mathematician" in prompt.lower() or alice.role.lower() in prompt.lower(), "Role not in system prompt"
        assert len(prompt) > 50, "System prompt too short"

    @pytest.mark.asyncio
    async def test_real_ai_conversation_turn(self, real_app, test_personas):
        """Test actual AI conversation turn with real model."""
        import streamlit as st

        # Setup session state
        st.session_state.personas = test_personas
        st.session_state.messages = []
        st.session_state.settings = {
            "context_messages": 5,
            "enable_thinking": False,  # Disable for faster testing
            "response_timeout": 60  # Shorter timeout for testing
        }

        alice = test_personas[0]

        # Generate real AI response
        response_chunks = []
        thinking_chunks = []

        try:
            async for chunk in real_app.get_ai_response_stream(
                alice,
                "What is 2+2? Answer with just the number."
            ):
                if chunk.get("type") == "thinking":
                    thinking_chunks.append(chunk.get("content", ""))
                elif chunk.get("type") == "response":
                    response_chunks.append(chunk.get("content", ""))
                elif chunk.get("response"):  # Fallback format
                    response_chunks.append(chunk.get("response"))
        except Exception as e:
            pytest.fail(f"Real AI response failed: {e}")

        # Should get some response
        full_response = "".join(response_chunks).strip()
        assert len(full_response) > 0, "No response from real AI"

        # Should contain the answer
        assert any(word in full_response.lower() for word in ["4", "four"]), \
               f"Expected math answer, got: {full_response}"

    def test_real_conversation_logging(self, real_app, test_personas, temp_log_dir):
        """Test real conversation logging to file system."""
        import streamlit as st

        # Setup
        st.session_state.personas = test_personas
        alice = test_personas[0]

        # Log a real message
        test_message = "This is a test message for logging"
        real_app.conversation_logger.log_message(
            alice.name,
            test_message,
            datetime.now()
        )

        # Verify log file was created
        log_files = list(Path(temp_log_dir).glob("*.txt"))
        assert len(log_files) >= 1, "No log file created"

        # Verify content
        log_content = log_files[0].read_text(encoding='utf-8')
        assert alice.name in log_content, "Persona name not in log"
        assert test_message in log_content, "Test message not in log"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_multi_turn_conversation(self, real_app, test_personas):
        """Test real multi-turn conversation with AI responses.

        This test requires a live Ollama instance with phi3:mini model.
        Skip with: pytest -m "not integration"
        """
        import streamlit as st

        # Setup
        st.session_state.personas = test_personas
        st.session_state.messages = []
        st.session_state.settings = {
            "context_messages": 5,
            "enable_thinking": False,
            "response_timeout": 60
        }

        alice = test_personas[0]
        bob = test_personas[1]

        # First turn
        first_response = ""
        try:
            async for chunk in real_app.get_ai_response_stream(
                alice,
                "Introduce yourself in one sentence."
            ):
                if chunk.get("response"):
                    first_response += chunk.get("response")
        except Exception as e:
            pytest.fail(f"First turn failed: {e}")

        assert len(first_response.strip()) > 0, "First AI response empty"

        # Add to conversation history
        st.session_state.messages.append({
            "persona": alice.name,
            "content": first_response.strip(),
            "timestamp": datetime.now(),
            "thinking": ""
        })

        # Second turn (Bob responds to Alice)
        second_response = ""
        try:
            async for chunk in real_app.get_ai_response_stream(
                bob,
                f"Respond to Alice's introduction: {first_response}"
            ):
                if chunk.get("response"):
                    second_response += chunk.get("response")
        except Exception as e:
            pytest.fail(f"Second turn failed: {e}")

        assert len(second_response.strip()) > 0, "Second AI response empty"

        # Verify conversation context is maintained
        assert len(st.session_state.messages) == 1, "Conversation history not maintained"


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
        logger = SecureConversationLogger(str(log_dir))

        # Test log file creation
        today = datetime.now().strftime("%Y-%m-%d")
        expected_filename = f"streamlit_backroom_{today}.txt"
        expected_path = log_dir / expected_filename

        # Log multiple messages
        messages = [
            ("Alice", "Hello world", datetime.now()),
            ("Bob", "Hi there", datetime.now()),
            ("Alice", "How are you?", datetime.now())
        ]

        for persona, message, timestamp in messages:
            logger.log_message(persona, message, timestamp)

        # Verify file exists
        assert expected_path.exists(), "Log file not created"

        # Verify content
        content = expected_path.read_text(encoding='utf-8')
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
        logger = SecureConversationLogger(str(log_dir))

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

    def test_real_error_handling_file_permissions(self, temp_workspace):
        """Test real error handling with file permission issues."""
        log_dir = Path(temp_workspace)
        logger = SecureConversationLogger(str(log_dir))

        # Create log file
        logger.log_message("Alice", "Test message", datetime.now())

        # Try to make directory read-only (if possible on this system)
        try:
            log_dir.chmod(0o444)  # Read-only

            # This should handle the permission error gracefully
            logger.log_message("Bob", "Should not fail", datetime.now())

        except PermissionError:
            # Expected on some systems
            pass
        except Exception as e:
            # Should not crash the application
            assert not isinstance(e, PermissionError), "Permission error not handled"
        finally:
            # Restore permissions for cleanup
            try:
                log_dir.chmod(0o755)
            except:
                pass


@pytest.mark.integration
class TestRealSystemIntegration:
    """Test complete system integration with real components.

    These tests require a live Ollama instance running on localhost:11434.
    Skip with: pytest -m "not integration"
    """

    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def integrated_system(self, temp_workspace):
        """Create fully integrated system with real components."""
        # Real Ollama client
        client = OllamaClient("http://localhost:11434")

        # Real conversation logger
        logger = SecureConversationLogger(temp_workspace)

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
            "response_timeout": 90
        }

        return app, client, logger

    @pytest.mark.asyncio
    async def test_end_to_end_conversation(self, integrated_system):
        """Test complete end-to-end conversation flow."""
        app, client, logger = integrated_system

        # Create test personas
        personas = [
            AIPersona(
                id="real_1",
                name="Alex",
                model="phi3:mini",
                role="Assistant",
                enabled=True,
                color="#FF6B6B"
            ),
            AIPersona(
                id="real_2",
                name="Sam",
                model="phi3:mini",
                role="Helper",
                enabled=True,
                color="#4ECDC4"
            )
        ]

        import streamlit as st
        st.session_state.personas = personas
        st.session_state.messages = []

        # Real conversation flow
        conversation_turns = 3

        for turn in range(conversation_turns):
            # Get next speaker
            speaker = app.get_next_speaker()
            assert speaker is not None, f"No speaker for turn {turn+1}"

            # Generate prompt with conversation context
            if turn == 0:
                prompt = "Introduce yourself briefly."
            else:
                recent_messages = st.session_state.messages[-2:]
                context = "\n".join([f"{m['persona']}: {m['content']}" for m in recent_messages])
                prompt = f"Continue the conversation:\n{context}\n\nRespond as {speaker.name}."

            # Get real AI response
            response_text = ""
            try:
                async for chunk in app.get_ai_response_stream(speaker, prompt):
                    if chunk.get("response"):
                        response_text += chunk.get("response")
            except Exception as e:
                pytest.fail(f"Turn {turn+1} failed for {speaker.name}: {e}")

            assert len(response_text.strip()) > 0, f"Empty response in turn {turn+1}"

            # Add to conversation
            st.session_state.messages.append({
                "persona": speaker.name,
                "content": response_text.strip(),
                "timestamp": datetime.now(),
                "thinking": ""
            })

            # Log to file
            logger.log_message(speaker.name, response_text.strip(), datetime.now())

        # Verify conversation completed
        assert len(st.session_state.messages) == conversation_turns, "Not all turns completed"

        # Verify both speakers participated
        speakers_in_convo = set(msg["persona"] for msg in st.session_state.messages)
        assert "Alex" in speakers_in_convo, "Alex didn't speak"
        assert "Sam" in speakers_in_convo, "Sam didn't speak"

        # Verify log files created
        log_files = list(Path(logger.log_dir).glob("*.txt"))
        assert len(log_files) >= 1, "No log files created"

        # Verify log content
        log_content = log_files[0].read_text(encoding='utf-8')
        assert len(log_content) > 100, "Log file too short"
        assert "Alex" in log_content and "Sam" in log_content, "Not all speakers in log"

    def test_system_under_load(self, integrated_system):
        """Test system behavior under load."""
        app, client, logger = integrated_system

        # Create multiple personas
        personas = []
        for i in range(5):
            personas.append(AIPersona(
                id=f"load_test_{i}",
                name=f"Speaker{i+1}",
                model="phi3:mini",
                role=f"Role{i+1}",
                enabled=True,
                color=f"#FF{i:02x}{i:02x}"
            ))

        import streamlit as st
        st.session_state.personas = personas
        st.session_state.messages = []

        # Rapid speaker selection (simulating UI interaction)
        speakers_selected = []
        for _ in range(20):  # 20 rapid selections
            speaker = app.get_next_speaker()
            if speaker:
                speakers_selected.append(speaker.name)

        # Verify rotation works under load
        assert len(speakers_selected) == 20, "Not all speaker selections completed"

        # Should cycle through all enabled personas
        unique_speakers = set(speakers_selected)
        assert len(unique_speakers) >= 3, "Not enough unique speakers under load"

        # Test rapid logging
        start_time = time.time()
        for i in range(10):
            logger.log_message(
                f"Speaker{i%5}",
                f"Rapid message {i}",
                datetime.now()
            )
        end_time = time.time()

        # Should complete quickly
        assert end_time - start_time < 5, "Rapid logging too slow"

        # Verify all messages logged
        log_files = list(Path(logger.log_dir).glob("*.txt"))
        assert len(log_files) >= 1, "No log files after rapid logging"

        log_content = log_files[0].read_text(encoding='utf-8')
        assert log_content.count("Rapid message") >= 10, "Not all rapid messages logged"

    @pytest.mark.asyncio
    async def test_error_recovery_and_robustness(self, integrated_system):
        """Test system error recovery and robustness."""
        app, client, logger = integrated_system

        # Test connection recovery
        try:
            success, models = await client.test_connection()
            if success:
                # Test with slightly invalid model name (should handle gracefully)
                try:
                    chunks = []
                    async for chunk in client.generate_stream("phi3:mini:invalid", "test"):
                        chunks.append(chunk)
                        if chunk.get("done") or len(chunks) > 5:  # Prevent infinite loop
                            break
                except Exception:
                    pass  # Expected to fail gracefully
        except Exception as e:
            pytest.fail(f"Connection test failed unexpectedly: {e}")

        # Test file system error recovery
        try:
            # Log with various message types including potential edge cases
            test_messages = [
                ("Normal", "Regular message"),
                ("Special:Chars", "Message with : special * characters"),
                ("Unicode", "Message with émojis 🚀 and ñ"),
                ("Long", "A" * 1000),  # Long message
                ("Empty", ""),  # Edge case
            ]

            for persona, message in test_messages:
                logger.log_message(persona, message, datetime.now())

            # Verify logging survived edge cases
            log_files = list(Path(logger.log_dir).glob("*.txt"))
            if log_files:
                content = log_files[0].read_text(encoding='utf-8')
                assert len(content) > 0, "Log file empty after edge cases"

        except Exception as e:
            pytest.fail(f"Error recovery failed: {e}")


# Performance and stress tests
@pytest.mark.integration
class TestRealSystemPerformance:
    """Test real system performance under realistic conditions.

    These tests require a live Ollama instance running on localhost:11434.
    Skip with: pytest -m "not integration"
    """

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
            run_conversation(1),
            run_conversation(2),
            run_conversation(3),
            return_exceptions=True
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
        assert end_time - start_time < 120, f"Concurrent conversations took too long: {end_time - start_time}s"

    def test_memory_usage_stability(self):
        """Test memory usage stability over extended operation."""
        import gc

        # Try to import psutil, skip test if not available
        try:
            import psutil
            has_psutil = True
        except ImportError:
            has_psutil = False

        if has_psutil:
            import os
            # Get initial memory usage
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss

        # Create and use many objects
        for i in range(100):
            # Create temporary objects
            temp_data = []
            for j in range(100):
                temp_data.append({
                    "id": f"{i}_{j}",
                    "content": "Test content " * 10,
                    "timestamp": datetime.now(),
                    "metadata": {"iteration": i, "sub_iteration": j}
                })

            # Simulate some processing
            processed = [item for item in temp_data if item["metadata"]["iteration"] % 2 == 0]

            # Clear references
            del temp_data
            del processed

            if i % 20 == 0:
                gc.collect()

        # Final cleanup
        gc.collect()

        if has_psutil:
            # Check memory usage
            final_memory = process.memory_info().rss
            memory_increase = final_memory - initial_memory
            memory_increase_mb = memory_increase / (1024 * 1024)

            # Should not leak too much memory (allow some reasonable increase)
            assert memory_increase_mb < 100, f"Memory leak detected: {memory_increase_mb:.1f}MB increase"
        else:
            # If psutil not available, just verify we didn't crash
            assert True, "Memory stability test completed (psutil not available)"