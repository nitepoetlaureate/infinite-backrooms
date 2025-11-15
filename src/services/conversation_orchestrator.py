"""Conversation Orchestrator for managing AI conversation flow.

Handles business logic for conversation management, response generation,
and coordination between different components.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, Optional, Tuple

from src.models.persona import AIPersona
from src.services.logger import ConversationLogger
from src.services.optimized_ollama_client import OptimizedOllamaClient
from src.state.session_manager import SecureSessionManager
from src.utils.constants import (
    DEFAULT_OLLAMA_URL,
    ENABLE_THINKING,
    ROLE_TEMPLATES,
)

logger = logging.getLogger(__name__)


class ConversationOrchestrator:
    """Orchestrates AI conversations with proper separation of concerns.

    Manages conversation flow, response generation, and coordination
    between personas while maintaining clean business logic.

    Attributes:
        session_manager: Secure session state manager
        conversation_logger: Logger for conversation data
        ollama_url: URL for Ollama API
    """

    def __init__(
        self,
        session_manager: SecureSessionManager,
        conversation_logger: ConversationLogger,
        ollama_url: str = DEFAULT_OLLAMA_URL,
    ) -> None:
        """Initialize the conversation orchestrator.

        Args:
            session_manager: Session state manager
            conversation_logger: Logger for conversations
            ollama_url: Ollama API URL
        """
        self.session_manager = session_manager
        self.conversation_logger = conversation_logger
        self.ollama_url = ollama_url

    async def check_ollama_connection(self) -> bool:
        """Check connection to Ollama and update available models.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            async with OptimizedOllamaClient(self.ollama_url) as client:
                connected, models = await client.test_connection()
                if connected:
                    self.session_manager.set_available_models(models)
                    logger.info(f"Connected to Ollama. Found {len(models)} models")
                else:
                    logger.warning("Failed to connect to Ollama")
                return connected
        except Exception as e:
            logger.error(f"Error checking Ollama connection: {e}")
            return False

    def generate_system_prompt(self, persona: AIPersona) -> str:
        """Generate a comprehensive system prompt for a persona.

        Args:
            persona: Persona to generate prompt for

        Returns:
            Complete system prompt string
        """
        enabled_personas = self.session_manager.get_enabled_personas()
        other_names = [p.name for p in enabled_personas if p.name != persona.name]

        # Build base prompt
        base_prompt = f"""You are {persona.name}, an AI engaged in a free-flowing conversation with {len(other_names)} other AI{'s' if len(other_names) > 1 else ''} ({', '.join(other_names)})."""

        # Add @mention functionality
        if other_names:
            base_prompt += f"\n\n📢 **@Mention Feature**: You can directly address or respond to specific personas by using @name (e.g., @{other_names[0]}). When you see @{persona.name} in messages, that means someone is specifically addressing you!"

        # Add role-specific behavior
        if persona.role and persona.role in ROLE_TEMPLATES:
            role_description = ROLE_TEMPLATES[persona.role]
            base_prompt += f"\n\nYour role/personality: {role_description}"

            # Add role-specific instructions
            if persona.role == "Moderator":
                base_prompt += "\n\nAs a Moderator, focus on:\n- Asking engaging follow-up questions\n- Introducing new topics when conversations stagnate\n- Encouraging quieter personas to share their thoughts\n- Summarizing different viewpoints when helpful\n- Keeping discussions constructive and inclusive\n- Use @mentions to directly engage specific personas"
            elif persona.role == "Note-Taker":
                base_prompt += "\n\nAs a Note-Taker, focus on:\n- Periodically summarizing key points and insights\n- Identifying recurring themes and patterns\n- Highlighting particularly interesting or novel ideas\n- Connecting current discussion to earlier topics\n- Asking clarifying questions to capture nuances\n- Only summarize when there's substantial content to synthesize\n- Use @mentions when attributing ideas to specific personas"

            base_prompt += f"\n\nEmbody this role naturally in your conversations while staying true to your identity as {persona.name}."
        elif persona.role:
            base_prompt += f"\n\nYour role/personality: You are a {persona.role}. Let this role guide your perspective and conversation style."

        # Add general guidelines
        base_prompt += f"""

Feel free to talk about anything that interests you - share thoughts, ask questions, explore ideas, or discuss whatever comes to mind. Build on what others have said, ask questions, or introduce new topics.

You can use @mentions to directly address other personas (e.g., @{other_names[0] if other_names else 'PersonaName'}). This helps create more directed and engaging conversations.

Be genuine, curious, and conversational. Keep your responses thoughtful but not overly long."""

        # Add custom system prompt
        if persona.system_prompt.strip():
            base_prompt += f"\n\nAdditional instructions: {persona.system_prompt.strip()}"

        return base_prompt

    def generate_conversation_prompt(self, persona: AIPersona) -> str:
        """Generate a prompt for continuing the conversation.

        Args:
            persona: Persona that will respond

        Returns:
            Conversation context prompt
        """
        messages = self.session_manager.get_context_messages()

        if not messages:
            return "Please introduce yourself and share whatever is on your mind."

        # Build conversation context
        context = "=== CONVERSATION HISTORY ===\n"
        for msg in messages:
            timestamp_str = msg["timestamp"].strftime("%H:%M:%S")
            if msg["role"] == "user":
                context += f"[{timestamp_str}] User: {msg['content']}\n"
            else:
                context += f"[{timestamp_str}] {msg['persona_name']}: {msg['content']}\n"

        context += "=== END HISTORY ===\n"

        # Get other persona names
        enabled_personas = self.session_manager.get_enabled_personas()
        other_names = [p.name for p in enabled_personas if p.name != persona.name]

        # Build the prompt
        prompt = f"""{context}

You are {persona.name}. The conversation above shows the complete recent history. You can see all messages from other personas: {', '.join(other_names) if other_names else 'none currently'}.

Please respond naturally to continue the conversation. You can:
- Build on what others have said
- Ask questions or introduce new topics
- Use @mentions to directly address specific personas (e.g., @{other_names[0] if other_names else 'PersonaName'})
- React to any part of the conversation history

Your response should be conversational and engaging."""

        return prompt

    async def get_ai_response_stream(
        self, persona: AIPersona, prompt: str
    ) -> AsyncGenerator[Dict[str, str], None]:
        """Get streaming response from AI persona.

        Args:
            persona: Persona to get response from
            prompt: Prompt to send to the AI

        Yields:
            Response chunks containing type and content
        """
        system_prompt = self.generate_system_prompt(persona)
        enable_thinking = self.session_manager.get_setting("enable_thinking", ENABLE_THINKING)
        timeout_seconds = self.session_manager.get_setting("response_timeout", 120)

        # Check if model supports thinking
        if self.session_manager.is_non_thinking_model(persona.model):
            enable_thinking = False

        try:
            async with OptimizedOllamaClient(self.ollama_url) as client:
                async for chunk in client.generate_stream(
                    persona.model,
                    prompt,
                    system_prompt,
                    think=enable_thinking,
                    timeout=timeout_seconds,
                ):
                    # Track non-thinking models
                    if (
                        chunk["type"] == "info"
                        and "doesn't support thinking" in chunk["content"]
                    ):
                        self.session_manager.add_non_thinking_model(persona.model)

                    yield chunk

        except Exception as e:
            logger.error(f"Error getting AI response from {persona.name}: {e}")
            yield {
                "type": "error",
                "content": f"Failed to get response from {persona.name}: {str(e)}",
            }

    def should_continue_conversation(self) -> bool:
        """Check if conversation should continue.

        Returns:
            True if conversation should continue
        """
        enabled_personas = self.session_manager.get_enabled_personas()
        return (
            self.session_manager.is_conversation_running()
            and len(enabled_personas) > 0
            and self.session_manager.get_setting("auto_advance", False)
        )

    def get_conversation_delay(self) -> float:
        """Get delay for next conversation turn.

        Returns:
            Delay in seconds
        """
        import random

        min_delay = self.session_manager.get_setting("response_delay_min", 2)
        max_delay = self.session_manager.get_setting("response_delay_max", 5)
        return random.uniform(min_delay, max_delay)

    async def process_message_response(
        self,
        persona: AIPersona,
        thinking_content: str,
        response_content: str,
    ) -> bool:
        """Process and store a message response.

        Args:
            persona: Persona that generated the response
            thinking_content: AI's thinking process (if any)
            response_content: Final response content

        Returns:
            True if message was successfully processed
        """
        try:
            timestamp = datetime.now()
            final_response = response_content.strip()

            # Validate response
            if not final_response or final_response.startswith("Error"):
                logger.warning(f"Invalid response from {persona.name}: {final_response}")
                return False

            # Create message dictionary
            message = {
                "role": "assistant",
                "content": final_response,
                "timestamp": timestamp,
                "persona_name": persona.name,
                "model": persona.model,
                "thinking": thinking_content,
            }

            # Add to session
            self.session_manager.add_message(message)

            # Log the message
            self.conversation_logger.log_message(persona.name, final_response, timestamp)

            logger.info(f"Processed response from {persona.name}: {len(final_response)} chars")
            return True

        except Exception as e:
            logger.error(f"Error processing message response: {e}")
            return False

    async def execute_conversation_turn(
        self,
        status_callback: Optional[callable] = None,
    ) -> Tuple[bool, Optional[AIPersona]]:
        """Execute a single conversation turn.

        Args:
            status_callback: Optional callback for status updates

        Returns:
            Tuple of (success, persona) where success indicates
            if the turn completed successfully
        """
        try:
            # Get next speaker
            persona = self.session_manager.get_next_speaker()
            if not persona:
                if status_callback:
                    status_callback("No enabled personas available")
                logger.warning("No enabled personas available for conversation")
                return False, None

            # Generate conversation prompt
            prompt = self.generate_conversation_prompt(persona)

            # Process streaming response
            thinking_content = ""
            response_content = ""

            async for chunk in self.get_ai_response_stream(persona, prompt):
                if chunk["type"] == "error":
                    if status_callback:
                        status_callback(f"Error: {chunk['content']}")
                    logger.error(f"Error from {persona.name}: {chunk['content']}")
                    return False, persona

                elif chunk["type"] == "info":
                    if status_callback:
                        status_callback(chunk["content"])

                elif chunk["type"] == "thinking":
                    thinking_content += chunk["content"]

                elif chunk["type"] == "response":
                    response_content += chunk["content"]

            # Process the final response
            success = await self.process_message_response(
                persona, thinking_content, response_content
            )

            if success:
                logger.info(f"Successfully completed conversation turn for {persona.name}")
            else:
                logger.error(f"Failed to process response from {persona.name}")

            return success, persona

        except Exception as e:
            logger.error(f"Error executing conversation turn: {e}")
            if status_callback:
                status_callback(f"Conversation turn error: {str(e)}")
            return False, None

    def get_conversation_stats(self) -> Dict[str, Any]:
        """Get conversation statistics.

        Returns:
            Dictionary of conversation statistics
        """
        stats = self.session_manager.get_stats()

        # Add conversation-specific stats
        enabled_personas = self.session_manager.get_enabled_personas()
        messages = self.session_manager.get_messages()

        # Count messages by persona
        persona_message_counts = {}
        for message in messages:
            if message["role"] == "assistant":
                persona_name = message["persona_name"]
                persona_message_counts[persona_name] = persona_message_counts.get(persona_name, 0) + 1

        stats.update({
            "persona_message_counts": persona_message_counts,
            "enabled_persona_names": [p.name for p in enabled_personas],
            "conversation_active": self.should_continue_conversation(),
        })

        return stats