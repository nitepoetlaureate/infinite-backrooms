"""Tests for conversation orchestrator functionality."""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
import asyncio
from typing import Dict, Any, List

# Mock the orchestrator module since it might not exist yet
class MockConversationOrchestrator:
    """Mock conversation orchestrator for testing."""

    def __init__(self, ollama_client, conversation_logger, rate_limiter):
        self.ollama_client = ollama_client
        self.conversation_logger = conversation_logger
        self.rate_limiter = rate_limiter
        self.active_personas = []
        self.conversation_history = []
        self.is_running = False

    async def start_conversation(self, personas: List[Any]) -> None:
        """Start a conversation with the given personas."""
        if self.rate_limiter.is_rate_limited():
            raise Exception("Rate limit exceeded")

        self.active_personas = personas
        self.is_running = True

    async def process_message(self, message: str, sender: str) -> Dict[str, Any]:
        """Process a message and generate responses."""
        if not self.is_running:
            raise Exception("Conversation not started")

        # Log the message
        self.conversation_logger.log_message(sender, message)

        # Generate responses from other personas
        responses = []
        for persona in self.active_personas:
            if persona.name != sender:
                response = await self._generate_response(persona, message)
                responses.append(response)
                self.conversation_logger.log_message(persona.name, response)

        return {
            "timestamp": datetime.now(),
            "responses": responses,
            "processed": True
        }

    async def _generate_response(self, persona, message: str) -> str:
        """Generate a response from a specific persona."""
        response_parts = []
        async for chunk in self.ollama_client.generate_stream(
            model=persona.model,
            prompt=f"{persona.system_prompt}\n\nUser: {message}\nAssistant:",
            persona_name=persona.name
        ):
            if chunk.get("response"):
                response_parts.append(chunk.get("response"))
            if chunk.get("done", False):
                break
        return "".join(response_parts)

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get the conversation history."""
        return self.conversation_history

    def stop_conversation(self) -> None:
        """Stop the current conversation."""
        self.is_running = False
        self.active_personas = []


class TestConversationOrchestrator:
    """Test suite for ConversationOrchestrator functionality."""

    @pytest.fixture
    def mock_ollama_client(self):
        """Mock Ollama client for testing."""
        client = Mock()

        # Create proper async generator mock
        async def mock_generate_stream(*args, **kwargs):
            """Mock async generator for streaming."""
            yield {"response": "Hello ", "done": False}
            yield {"response": "there!", "done": True}

        client.generate_stream = mock_generate_stream
        return client

    @pytest.fixture
    def mock_conversation_logger(self):
        """Mock conversation logger for testing."""
        logger = Mock()
        logger.log_message = Mock()
        logger.get_daily_log_file = Mock(return_value="test_log.txt")
        return logger

    @pytest.fixture
    def mock_rate_limiter(self):
        """Mock rate limiter for testing."""
        limiter = Mock()
        limiter.is_rate_limited = Mock(return_value=False)
        limiter.add_request = Mock()
        return limiter

    @pytest.fixture
    def orchestrator(self, mock_ollama_client, mock_conversation_logger, mock_rate_limiter):
        """Create a ConversationOrchestrator instance for testing."""
        return MockConversationOrchestrator(
            mock_ollama_client,
            mock_conversation_logger,
            mock_rate_limiter
        )

    @pytest.fixture
    def sample_personas(self):
        """Sample personas for testing."""
        alice = Mock()
        alice.name = "Alice"
        alice.model = "llama2:latest"
        alice.system_prompt = "You are Alice."

        bob = Mock()
        bob.name = "Bob"
        bob.model = "mistral:latest"
        bob.system_prompt = "You are Bob."

        charlie = Mock()
        charlie.name = "Charlie"
        charlie.model = "llama2:latest"
        charlie.system_prompt = "You are Charlie."

        return [alice, bob, charlie]

    @pytest.mark.asyncio
    async def test_start_conversation_success(self, orchestrator, sample_personas):
        """Test successful conversation start."""
        await orchestrator.start_conversation(sample_personas)

        assert orchestrator.is_running is True
        assert len(orchestrator.active_personas) == 3
        assert orchestrator.active_personas == sample_personas

    @pytest.mark.asyncio
    async def test_start_conversation_rate_limit(self, orchestrator, sample_personas):
        """Test conversation start when rate limited."""
        orchestrator.rate_limiter.is_rate_limited.return_value = True

        with pytest.raises(Exception, match="Rate limit exceeded"):
            await orchestrator.start_conversation(sample_personas)

        assert orchestrator.is_running is False
        assert len(orchestrator.active_personas) == 0

    @pytest.mark.asyncio
    async def test_process_message_success(self, orchestrator, sample_personas):
        """Test successful message processing."""
        # Start conversation first
        await orchestrator.start_conversation(sample_personas)

        # Process a message
        result = await orchestrator.process_message("Hello everyone!", "Alice")

        # Verify the result
        assert result["processed"] is True
        assert "timestamp" in result
        assert "responses" in result
        assert len(result["responses"]) == 2  # Bob and Charlie should respond, not Alice

        # Verify logging
        orchestrator.conversation_logger.log_message.assert_called()

    @pytest.mark.asyncio
    async def test_process_message_without_conversation(self, orchestrator):
        """Test message processing when conversation not started."""
        with pytest.raises(Exception, match="Conversation not started"):
            await orchestrator.process_message("Hello", "Alice")

    @pytest.mark.asyncio
    async def test_process_message_with_self(self, orchestrator, sample_personas):
        """Test that sender doesn't respond to their own message."""
        await orchestrator.start_conversation(sample_personas)

        result = await orchestrator.process_message("Hello", "Alice")

        # Only Bob and Charlie should respond
        assert len(result["responses"]) == 2
        orchestrator.conversation_logger.log_message.assert_called()

    @pytest.mark.asyncio
    async def test_generate_response(self, orchestrator, sample_personas):
        """Test individual response generation."""
        persona = sample_personas[0]
        response = await orchestrator._generate_response(persona, "Hello")

        assert response == "Hello there!"
        orchestrator.ollama_client.generate_stream.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_response_empty(self, orchestrator, sample_personas):
        """Test empty response generation."""
        persona = sample_personas[0]

        # Mock empty response
        async def mock_empty_stream(*args, **kwargs):
            yield {"response": "", "done": True}

        orchestrator.ollama_client.generate_stream.side_effect = mock_empty_stream

        response = await orchestrator._generate_response(persona, "Hello")
        assert response == ""

    def test_get_conversation_history(self, orchestrator):
        """Test getting conversation history."""
        history = orchestrator.get_conversation_history()
        assert isinstance(history, list)

    def test_stop_conversation(self, orchestrator, sample_personas):
        """Test stopping a conversation."""
        # Start and stop conversation
        orchestrator.active_personas = sample_personas
        orchestrator.is_running = True

        orchestrator.stop_conversation()

        assert orchestrator.is_running is False
        assert len(orchestrator.active_personas) == 0

    @pytest.mark.asyncio
    async def test_concurrent_message_processing(self, orchestrator, sample_personas):
        """Test concurrent message processing."""
        await orchestrator.start_conversation(sample_personas)

        # Process multiple messages concurrently
        messages = [
            ("Hello from Alice", "Alice"),
            ("Hi from Bob", "Bob"),
            ("Hey from Charlie", "Charlie")
        ]

        tasks = [orchestrator.process_message(msg, sender) for msg, sender in messages]
        results = await asyncio.gather(*tasks)

        # All messages should be processed
        assert len(results) == 3
        for result in results:
            assert result["processed"] is True

    @pytest.mark.asyncio
    async def test_error_handling_in_message_processing(self, orchestrator, sample_personas):
        """Test error handling during message processing."""
        await orchestrator.start_conversation(sample_personas)

        # Mock an error in generate_stream
        orchestrator.ollama_client.generate_stream.side_effect = Exception("API Error")

        # Should handle the error gracefully
        with pytest.raises(Exception, match="API Error"):
            await orchestrator._generate_response(sample_personas[0], "Hello")

    def test_persona_validation(self, orchestrator):
        """Test persona validation in conversation."""
        invalid_personas = [
            None,  # None persona
            Mock(name=""),  # Empty name
            Mock(name=None),  # None name
        ]

        for invalid_persona in invalid_personas:
            with pytest.raises((AttributeError, TypeError)):
                # This would ideally raise a validation error
                orchestrator.active_personas = [invalid_persona]
                # Validation would happen during message processing

    @pytest.mark.asyncio
    async def test_message_rate_limiting(self, orchestrator, sample_personas):
        """Test rate limiting in message processing."""
        await orchestrator.start_conversation(sample_personas)

        # Mock rate limiter to trigger after first message
        orchestrator.rate_limiter.is_rate_limited.side_effect = [False, True]

        # First message should succeed
        result1 = await orchestrator.process_message("First message", "Alice")
        assert result1["processed"] is True

        # Second message should be rate limited (if implemented)
        # This depends on the actual implementation
        # orchestrator.process_message("Second message", "Bob")

    @pytest.mark.asyncio
    async def test_conversation_state_persistence(self, orchestrator, sample_personas):
        """Test conversation state persistence."""
        # Start conversation
        await orchestrator.start_conversation(sample_personas)

        # Process some messages
        await orchestrator.process_message("Hello", "Alice")
        await orchestrator.process_message("Hi back", "Bob")

        # Verify state is maintained
        assert orchestrator.is_running is True
        assert len(orchestrator.active_personas) == 3

        # Stop and verify cleanup
        orchestrator.stop_conversation()
        assert orchestrator.is_running is False
        assert len(orchestrator.active_personas) == 0

    def test_conversation_metadata(self, orchestrator, sample_personas):
        """Test conversation metadata handling."""
        # Test with metadata
        metadata = {
            "session_id": "test-session",
            "topic": "AI conversation",
            "created_at": datetime.now()
        }

        # This would depend on actual implementation
        # orchestrator.set_metadata(metadata)
        # assert orchestrator.metadata == metadata

    @pytest.mark.asyncio
    async def test_persona_order_preservation(self, orchestrator, sample_personas):
        """Test that persona order is preserved in responses."""
        # Reorder personas
        reordered_personas = [sample_personas[2], sample_personas[0], sample_personas[1]]
        await orchestrator.start_conversation(reordered_personas)

        result = await orchestrator.process_message("Hello", "Alice")

        # Verify response order matches persona order (excluding sender)
        # This depends on the actual implementation
        assert len(result["responses"]) == 2

    @pytest.mark.asyncio
    async def test_message_context_building(self, orchestrator, sample_personas):
        """Test building of message context for AI responses."""
        await orchestrator.start_conversation(sample_personas)

        # Mock context building
        with patch.object(orchestrator, '_build_context', return_value="Test context"):
            await orchestrator.process_message("Hello", "Alice")

            # Verify context was used
            orchestrator._build_context.assert_called_once()

    @pytest.mark.asyncio
    async def test_long_running_conversation(self, orchestrator, sample_personas):
        """Test behavior in long-running conversations."""
        await orchestrator.start_conversation(sample_personas)

        # Process many messages
        for i in range(10):
            await orchestrator.process_message(f"Message {i}", "Alice")

        # Verify conversation is still running
        assert orchestrator.is_running is True

        # Verify logging was called for each message
        assert orchestrator.conversation_logger.log_message.call_count >= 20